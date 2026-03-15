# Product Requirements Document (PRD)

## Objectives

Crux is a companion app designed to allow climbers to log their climbs and obtain an analysis of their ascent. The application scores the climb across various metrics and dimensions, ultimately suggesting improvements for the user's ascents.

## User Flow

1. The user uploads a video of their climb.
2. The app analyzes the climbing route and the climber’s ascent.
3. The ascent is scored at every point in time using defined metrics.
4. The app identifies areas of improvement and presents them to the user.

## Domain Specifications

- **Disciplines:** The primary focus is bouldering to start, with potential extensions to other climbing types in the future.
- **Grading Systems:** Initial support is for the V-scale, with auto-conversion as a long-term consideration.
- **Environment:** Indoor climbs are prioritized, with outdoor climbs planned as an extension.

## Feature Specifications

### Client-Side (Upload & Feedback)

- Users can upload their climbs (Priority: P0).
- A UI overlay is displayed for route identification and analysis feedback (Priority: P0).
- Future iterations may include climber physical attributes (height, etc.) to factor into grading (Priority: P2).

### Backend & Analysis

- Server, S3 bucket, and Database setup for managing uploads and pointers (Priority: P0).
- Identification capabilities must track the climbing route and the climber's bodily movements (Priority: P0).
- The system must score the climber's movements continuously throughout the climb (Priority: P1).

## Long-Term Considerations

- Expanding into offline app capabilities and on-device machine learning models for faster use.
- Implementation of user profiles, long-term project logging, and social features.
