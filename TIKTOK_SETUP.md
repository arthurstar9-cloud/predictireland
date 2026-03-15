# TikTok Content Posting API Setup

## 1. Create a TikTok Developer Account

- Go to [developers.tiktok.com](https://developers.tiktok.com)
- Click "Log in" and sign in with your TikTok account (or create one)
- Accept the developer terms of service

## 2. Create an App

- From the developer portal dashboard, click **Manage apps** > **Connect an app**
- Fill in the app name (e.g. "PredictIreland Poster")
- Set the platform to **Web** (server-side posting)
- Add a redirect URI (can be `https://localhost/callback` for now)

## 3. Add the Content Posting API Product

- In your app settings, go to **Add products**
- Select **Content Posting API**
- Click **Add**

## 4. Configure Required Scopes

Request the following scopes:

- `video.publish` — publish content to TikTok
- `video.upload` — upload video/photo files

Both are required for automated posting.

## 5. App Description (for Approval)

Use something like this in the app description/use case field:

> This application automates content posting for a prediction market affiliate page (PredictIreland). It programmatically creates and publishes photo carousel posts and short video clips featuring prediction market odds, poll results, and event forecasts to drive engagement and affiliate traffic.

Be specific about what content you are posting and why. TikTok reviewers want to see a clear, legitimate use case.

## 6. Review Process

- Submit the app for review
- TikTok typically reviews within **1-3 business days**
- You will receive an email notification when approved or if changes are requested
- If rejected, read the feedback, update the description/scopes, and resubmit

## 7. Generate an Access Token

Once approved:

1. Use the OAuth 2.0 authorization flow to get an auth code:
   ```
   https://www.tiktok.com/v2/auth/authorize/?client_key=YOUR_CLIENT_KEY&scope=video.publish,video.upload&response_type=code&redirect_uri=YOUR_REDIRECT_URI
   ```
2. Open that URL in a browser and authorize the app with your TikTok account
3. You will be redirected to your redirect URI with a `code` parameter
4. Exchange the code for an access token:
   ```bash
   curl -X POST https://open.tiktokapis.com/v2/oauth/token/ \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "client_key=YOUR_CLIENT_KEY&client_secret=YOUR_CLIENT_SECRET&code=AUTH_CODE&grant_type=authorization_code&redirect_uri=YOUR_REDIRECT_URI"
   ```
5. The response contains `access_token` and `refresh_token` — save both

## 8. Add Token to .env

Add the following line to your `.env` file in the project root:

```
TIKTOK_ACCESS_TOKEN=your_access_token_here
```

Optionally also store the refresh token and client credentials:

```
TIKTOK_REFRESH_TOKEN=your_refresh_token_here
TIKTOK_CLIENT_KEY=your_client_key_here
TIKTOK_CLIENT_SECRET=your_client_secret_here
```

## 9. Automatic Switching in poster.py

Once `TIKTOK_ACCESS_TOKEN` is set in `.env`, `poster.py` will automatically switch from saving files locally to posting directly via the TikTok API. No code changes needed.

## 10. Direct Post Capability (Important)

TikTok photo carousel posting via API requires your app to be approved for the **"Direct Post"** capability. Without it, posts will go to the user's inbox as drafts rather than publishing immediately. Make sure to request Direct Post during the app review process or apply for it separately after initial approval.
