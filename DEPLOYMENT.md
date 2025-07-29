# Baseball Motion Capture Visualizer - Deployment Guide

Your mocap visualizer is now ready to be hosted online! Here are several options to deploy it:

## Option 1: Render (Recommended - Free)

1. Go to [render.com](https://render.com) and sign up/login
2. Click "New +" and select "Web Service"
3. Connect your GitHub account and select this repository: `cooper-710/Mocap`
4. Choose the branch: `cursor/create-google-link-8698`
5. Render will automatically detect the `render.yaml` configuration
6. Click "Deploy Web Service"
7. Your app will be available at: `https://your-app-name.onrender.com`

## Option 2: Railway (Alternative - Free)

1. Go to [railway.app](https://railway.app) and sign up/login
2. Click "New Project" → "Deploy from GitHub repo"
3. Select this repository: `cooper-710/Mocap`
4. Choose the branch: `cursor/create-google-link-8698`
5. Railway will use the `Procfile` for deployment
6. Your app will be available at: `https://your-app-name.up.railway.app`

## Option 3: Heroku (Alternative)

1. Go to [heroku.com](https://heroku.com) and create an account
2. Install Heroku CLI and run:
   ```bash
   heroku create your-app-name
   git push heroku cursor/create-google-link-8698:main
   ```
3. Your app will be available at: `https://your-app-name.herokuapp.com`

## What's Included

The deployment includes:
- ✅ Flask web application with motion capture API
- ✅ 3D visualization using Three.js
- ✅ All your motion capture data (cooper_baseball_motion.bvh, joint data)
- ✅ Production-ready configuration with gunicorn
- ✅ Automatic scaling and HTTPS

## After Deployment

Once deployed, you can:
1. Share the live URL with anyone
2. View the 3D baseball motion capture visualization
3. Load custom BVH files
4. Use all the interactive camera controls
5. Access the API endpoints for motion data

## API Endpoints Available

- `/` - Main 3D viewer
- `/viewer` - Alternative viewer page
- `/api/motion-data` - Complete motion data as JSON
- `/api/motion-frame/<frame>` - Specific frame data
- `/api/motion-summary` - Motion summary statistics
- `/api/health` - Health check

Your mocap visualizer will be accessible worldwide via a Google-searchable URL!