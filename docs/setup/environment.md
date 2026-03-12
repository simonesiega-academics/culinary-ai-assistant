# Development Setup Guide

This document contains all essential commands to set up the development
environment and run the project.

---

## 1. Create a Conda Virtual Environment

Create a dedicated virtual environment for the project:

``` bash
conda create -n ai-culinary-assistant python=3.13
```

Activate the environment:

``` bash
conda activate ai-culinary-assistant
```

Deactivate the environment:

``` bash
conda deactivate
```

Remove the environment (only if necessary):

``` bash
conda remove -n ai-culinary-assistant --all
```

## 2. Clone the Repository

``` bash
git clone https://github.com/simone-academics/hs-ai-culinary-assistant.git
cd hs-ai-culinary-assistant
```

## 3. Install Project Dependencies

Upgrade pip (recommended):

``` bash
python -m pip install --upgrade pip
```

Install all required packages from `requirements.txt`:

``` bash
pip install -r requirements.txt
```

Verify installed packages:

``` bash
pip list
```

## 4. Update Dependencies

Upgrade all dependencies listed in `requirements.txt`:

``` bash
pip install -r requirements.txt --upgrade
```

## 5. Freeze Dependencies (Optional -- For Reproducibility)

Generate an updated `requirements.txt` file:

``` bash
pip freeze > requirements.txt
```


## 6. Run the Project

Make sure the environment is active:

``` bash
conda activate ai-culinary-assistant
```

Run the main application:

``` bash
python main.py
```

Run the test version:

``` bash
python main_test.py
```

## 7. Using venv Instead of Conda (Alternative)

If Conda is not available, you can use Python's built-in virtual
environment.

Create virtual environment:

``` bash
python -m venv venv
```

Activate on Windows:

``` bash
venv\Scripts\activate
```

Activate on macOS/Linux:

``` bash
source venv/bin/activate
```

Install dependencies:

``` bash
pip install -r requirements.txt
```

Deactivate:

``` bash
deactivate
```

## 8. Useful Debug Commands

Check Python version:

``` bash
python --version
```

Check environment path:

Windows:

``` bash
where python
```

macOS/Linux:

``` bash
which python
```

Check installed Conda environments:

``` bash
conda env list
```

---

# Environment Ready 

You are now ready to develop and run **AI Culinary Assistant**.
