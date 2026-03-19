from __future__ import annotations

from flask import Flask, jsonify, request

from app.agents.agent_one import AgentOneAnalyzer
from app.agents.agent_two import AgentTwoDatabaseBridge
from app.core.config import Settings, load_settings
from app.models.recipe import AnalysisBatch
from app.repositories.mariadb_repository import MariaDBRepository


def create_app(settings: Settings | None = None) -> Flask:
    resolved_settings = settings or load_settings()

    app = Flask(__name__)

    repository = MariaDBRepository(
        host=resolved_settings.db_host,
        port=resolved_settings.db_port,
        user=resolved_settings.db_user,
        password=resolved_settings.db_password,
        database=resolved_settings.db_name,
    )
    agent_one = AgentOneAnalyzer(resolved_settings)
    agent_two = AgentTwoDatabaseBridge(repository, resolved_settings.db_default_category)

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = resolved_settings.cors_origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        return response

    @app.route("/api/v1/health", methods=["GET"])
    def healthcheck():
        return jsonify(
            {
                "status": "ok",
                "agent_1": "ready",
                "agent_2": "ready",
            }
        )

    @app.route("/api/v1/agent-1/analyze", methods=["POST", "OPTIONS"])
    def analyze_pdf():
        if request.method == "OPTIONS":
            return ("", 204)

        uploaded_file = request.files.get("file")
        if uploaded_file is None:
            return jsonify({"error": "Missing file in multipart request"}), 400

        filename = uploaded_file.filename or "uploaded.pdf"
        if not filename.lower().endswith(".pdf"):
            return jsonify({"error": "Only PDF files are accepted"}), 400

        try:
            batch = agent_one.analyze_pdf(uploaded_file.read(), filename)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except Exception as exc:
            return jsonify({"error": f"Agent 1 failed: {exc}"}), 500

        return jsonify(batch.to_dict())

    @app.route("/api/v1/agent-2/persist", methods=["POST", "OPTIONS"])
    def persist_analyzed_data():
        if request.method == "OPTIONS":
            return ("", 204)

        payload = request.get_json(silent=True)
        if payload is None:
            return jsonify({"error": "Expected JSON payload"}), 400

        try:
            batch = AnalysisBatch.from_dict(payload)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        result = agent_two.persist_analysis(batch)
        status_code = 200
        if result.failed and not result.persisted:
            status_code = 500
        elif result.failed:
            status_code = 207

        return jsonify(result.to_dict()), status_code

    @app.route("/api/v1/agent-1/ingest", methods=["POST", "OPTIONS"])
    def run_ingestion_pipeline():
        if request.method == "OPTIONS":
            return ("", 204)

        uploaded_file = request.files.get("file")
        if uploaded_file is None:
            return jsonify({"error": "Missing file in multipart request"}), 400

        filename = uploaded_file.filename or "uploaded.pdf"
        if not filename.lower().endswith(".pdf"):
            return jsonify({"error": "Only PDF files are accepted"}), 400

        try:
            analysis = agent_one.analyze_pdf(uploaded_file.read(), filename)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except Exception as exc:
            return jsonify({"error": f"Agent 1 failed: {exc}"}), 500

        persistence = agent_two.persist_analysis(analysis)

        status_code = 200
        if persistence.failed and not persistence.persisted:
            status_code = 500
        elif persistence.failed:
            status_code = 207

        return (
            jsonify(
                {
                    "analysis": analysis.to_dict(),
                    "persistence": persistence.to_dict(),
                }
            ),
            status_code,
        )

    return app


def main() -> None:
    settings = load_settings()
    app = create_app(settings)
    app.run(host=settings.api_host, port=settings.api_port)


if __name__ == "__main__":
    main()
