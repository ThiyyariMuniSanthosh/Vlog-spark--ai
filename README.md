# VlogSpark AI — Vercel Full-Stack Deployment

This is a Next.js App Router project intended to deploy as one Vercel project. It includes the frontend and server-side API routes.

## Actual generation flow
1. Browser uploads the user's narration directly to Vercel Blob using a short-lived client upload token.
2. `/api/generate` asks Gemini for a natural script and six visual prompts.
3. The backend submits six asynchronous Kling 3.0 Standard video jobs through fal.ai.
4. Browser polls `/api/video-status` until the six jobs complete.
5. `/api/render` submits a Shotstack edit containing six video clips plus the uploaded narration audio.
6. Browser polls `/api/render-status` and displays the final MP4 when ready.

Presenter scenes are generated fictional presenter footage, not guaranteed lip-synced avatar video. The user's uploaded voice is used as the narration track; no voice cloning is performed. SRT timing is estimated from script length, not speech recognition.

## Services and keys required
- Google AI Studio: `GEMINI_API_KEY`
- fal.ai: `FAL_KEY`
- Shotstack: `SHOTSTACK_API_KEY`
- Vercel Blob: connect a Blob store to the Vercel project. Vercel adds `BLOB_READ_WRITE_TOKEN` automatically.

The video generation and final rendering services may charge credits. Begin with the Shotstack `stage` environment, which returns a watermarked test render. Check current prices and account rules with a parent or guardian before activating paid services. Change `SHOTSTACK_ENV` to `v1` only after understanding the cost.

## Deploy to Vercel (beginner steps)
1. Download and extract the ZIP.
2. Create a GitHub repository for the extracted project and upload all files. Do not upload `.env` or API keys.
3. Open Vercel and choose **Add New → Project**.
4. Import your new GitHub repository. Framework should be detected as Next.js.
5. Open **Storage** in the Vercel project, create a **Blob** store, and connect it to this project. This creates `BLOB_READ_WRITE_TOKEN`.
6. Open **Settings → Environment Variables** and add:
   - `GEMINI_API_KEY`
   - `GEMINI_MODEL` = `gemini-2.5-flash`
   - `FAL_KEY`
   - `FAL_VIDEO_MODEL` = `fal-ai/kling-video/v3/standard/text-to-video`
   - `SHOTSTACK_API_KEY`
   - `SHOTSTACK_ENV` = `stage`
7. Redeploy after adding the environment variables.
8. Open the deployment URL and test `/api/health`. All four provider flags should be `true`.
9. Test with a short topic and a short voice recording. Wait while six clips are generated and then rendered.

## Local development
Requirements: Node.js 20.9+ and npm.

```bash
npm install
cp .env.example .env.local
# Edit .env.local with your keys
npm run dev
```

Open http://localhost:3000. For local Blob client uploads, connect a Blob store to the Vercel project and use `vercel env pull .env.local` after linking the project with the Vercel CLI.

## Project structure

```text
app/
  api/
    generate/route.js
    health/route.js
    render/route.js
    render-status/route.js
    upload/route.js
    video-status/route.js
  globals.css
  layout.js
  page.js
lib/
  providers.js
.env.example
.gitignore
next.config.mjs
package.json
vercel.json
README.md
```

## Important deployment and security notes
- Never put secret API keys in browser code or variables prefixed with `NEXT_PUBLIC_`.
- The narration is uploaded to a **public Blob URL** so the render provider can fetch it. Anyone who obtains that URL may be able to access the recording. Delete it from the Vercel Blob store when no longer needed. For a public product, replace this with private storage and a controlled signed-URL workflow.
- This starter has no login, per-user quotas, billing guard, or robust rate limiting. Do not share the public deployment widely until authentication and abuse protection are added; otherwise visitors may trigger usage charged to your API accounts.
- Add server-side authentication, per-user job limits, request validation, a durable job database, cleanup jobs, and monitoring before public launch.
- The six clip jobs are asynchronous; a browser tab needs to remain open for this starter's simple polling UI. A production version should store job state in a database and use provider webhooks.
- Vercel serverless functions are not used for heavy video transcoding. Shotstack handles final rendering externally.
- The project uses a public Blob upload workflow; test with non-sensitive recordings first.

## Troubleshooting
- `/api/health` has false flags: add the missing environment variable or connect Blob Storage, then redeploy.
- `Missing GEMINI_API_KEY`: check exact spelling and Production environment assignment.
- `FAL_KEY` errors: confirm your fal account/model access and credits.
- Shotstack `401`: check that the key matches `SHOTSTACK_ENV` (`stage` key with stage, production key with v1).
- Shotstack validation error: inspect the render route response and Shotstack API docs for schema changes.
- Generation cost: each run submits six Kling video jobs plus one Shotstack render. Stop testing if you do not understand the provider pricing.
