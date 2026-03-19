export type StructuredRecipe = {
  name: string;
  description: string | null;
  time_minutes: number | null;
  difficulty: number | null;
  ingredients: string[];
  procedure_steps: string[];
};

export type AnalysisBatch = {
  source: string;
  recipes: StructuredRecipe[];
};

export type PersistenceResult = {
  source: string;
  persisted: number;
  failed: number;
  recipe_names: string[];
  errors: string[];
};

export type FullIngestionResponse = {
  analysis: AnalysisBatch;
  persistence: PersistenceResult;
};
