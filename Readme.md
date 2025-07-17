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

<img width="1909" height="1149" alt="image" src="https://github.com/user-attachments/assets/84d8c9f9-1d51-4979-9f93-a357cfdc7d41" />


### API Endpoints
- **GET /**: Health check.
- **POST /predict**: Upload a CT scan image to get a prediction.

### Deployed on Render
- **https://lung-cancer-detection-s7se.onrender.com/docs**
