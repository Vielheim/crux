# Project Status & Plan

This document tracks the ongoing development tasks, their current status, and implementation notes.

## 1. Core Set-up

| Task              | Status       | Remarks |
| :---------------- | :----------- | :------ |
| Docker            | ✅ Completed |         |
| Project directory | ✅ Completed |         |
| Git               | ✅ Completed |         |

## 2. Backend Container

| Task                    | Status       | Remarks                               |
| :---------------------- | :----------- | :------------------------------------ |
| Container set-up        | ✅ Completed |                                       |
| Initial server endpoint | ✅ Completed |                                       |
| Database set-up         | ✅ Completed |                                       |
| Local S3 bucket         | ✅ Completed | Tested and verified upload with Minio |
| Redis queue set-up      | ✅ Completed | Put data into Redis                   |

## 3. Client Applications

| Task                  | Status       | Remarks                                     |
| :-------------------- | :----------- | :------------------------------------------ |
| Download React Native | 🛑 Blocked   | Paused, using web app for quick prototyping |
| Set up client app     | 🛑 Blocked   |                                             |
| Set up web app        | ✅ Completed |                                             |

## 4. Frontend Integration

| Task                                              | Status         | Remarks |
| :------------------------------------------------ | :------------- | :------ |
| Render video + overlay for climber identification | ✅ Completed   |         |
| Render video + overlay for route identification   | ⏳ Not Started |         |

## 5. User Flows

| Task                | Status         | Remarks                              |
| :------------------ | :------------- | :----------------------------------- |
| User creation flow  | ⏳ Not Started | TODO later                           |
| Video upload flow   | ✅ Completed   |                                      |
| Triggering analysis | ✅ Completed   | Read from Redis and perform analysis |

## 6. Analysis Engine

| Task                          | Status         | Remarks                                  |
| :---------------------------- | :------------- | :--------------------------------------- |
| Climber identification        | ✅ Completed   | Integrated MediaPipe for pose estimation |
| Climbing route identification | ⏳ Not Started |                                          |

## 7. Excellence Work

| Task         | Status         | Remarks |
| :----------- | :------------- | :------ |
| Set up CI/CD | ⏳ Not Started |         |
