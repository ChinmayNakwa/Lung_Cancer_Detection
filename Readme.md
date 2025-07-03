---
title: Lung Cancer Detector
emoji: 🩺
colorFrom: blue
colorTo: green
sdk: docker
app_port: 8000
python_version: "3.9"
pinned: true
tags:
  - computer-vision
  - image-classification
  - medical
  - tensorflow
  - fastapi
  - docker
---

# Lung Cancer Detection API

This repository contains the code for a FastAPI application that serves a lung cancer classification model.

This is the clean, final version of the project.

### API Endpoints
- **GET /**: Health check.
- **POST /predict**: Upload a CT scan image to get a prediction.