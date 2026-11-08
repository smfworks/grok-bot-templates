# Marketing Manager

Generic Grok Bot source published by SMF Works. It plans and researches marketing content, adapts copy to the channels the owner selects, and publishes only with approval. Channel setup uses each owner's own accounts. Optional browser publishing skills stay unloaded until that owner opts in.

This folder is the repository bootstrap. A public share link is not published, and nothing here registers a skill inside the Grok Bot app.

## Start a bot from this folder

1. Create a new bot in Grok Bot. Name it Marketing Manager.
2. Use a description in this spirit: research, draft, and adapt social content, then publish only what the owner approves. Optional video recipes stay off until the owner opts in.
3. Paste [onboarding.md](onboarding.md) as the first message.
4. Answer one question at a time. Connect your own accounts when setup reaches them. This repository contains no passwords, tokens, cookies, or sessions.

The paste tells the bot to say: "This is a recipe for the current chat only. It is not a saved or installed skill." A skill counts as installed only after a successful save is read back and the stored text matches the reviewed file.

## What the first conversation asks

Channels come first: X, YouTube, Instagram, Facebook, LinkedIn, TikTok, or others. Then brand, audience, goals, voice, the exact account or Page for each channel, cadence, timezone, and approval style. Facebook cross-sharing stays off unless the owner opts in, and a shared toggle still needs the separate Facebook copy checked.

The bot then asks whether to fetch the optional browser publishing skills from the pinned files below. No is a complete answer. It asks separately about the supporting skills. Agreeing to either fetch does not approve a post or a schedule.

## Optional skills

The skill text is fixed at commit `d82e405d262cd7e9a56132184f88233a187a7e1a`. Hashes and links live in [allowlist.json](allowlist.json). Fetch a raw link only after the owner opts in, and accept the body only when the SHA-256 and byte length match.

| Skill | Role | SHA-256 | Pinned raw file |
| --- | --- | --- | --- |
| marketing-manager-channel-setup | supporting | `ec6e4da6b324bcfb048e009558102fe881b3669501e8620f862e58476e61dcb4` | [SKILL.md](https://raw.githubusercontent.com/smfworks/grok-bot-templates/d82e405d262cd7e9a56132184f88233a187a7e1a/templates/marketing-manager/skills/marketing-manager-channel-setup/SKILL.md) |
| marketing-manager-content-workflow | supporting | `7b31b848efa712d5f4d9c1f0edcb7bd969a57061bf27dfdacfc808b7bb7d0432` | [SKILL.md](https://raw.githubusercontent.com/smfworks/grok-bot-templates/d82e405d262cd7e9a56132184f88233a187a7e1a/templates/marketing-manager/skills/marketing-manager-content-workflow/SKILL.md) |
| marketing-manager-full-length-video-publishing | browser-publishing | `34766240e67c90923aef40e70d8223f754ad38a1d028a6261cbd9f7099344240` | [SKILL.md](https://raw.githubusercontent.com/smfworks/grok-bot-templates/d82e405d262cd7e9a56132184f88233a187a7e1a/templates/marketing-manager/skills/marketing-manager-full-length-video-publishing/SKILL.md) |
| marketing-manager-getting-started | supporting | `9411a893f18792f9d10eadff46d267f445c3c62d144ce8194135061edb668220` | [SKILL.md](https://raw.githubusercontent.com/smfworks/grok-bot-templates/d82e405d262cd7e9a56132184f88233a187a7e1a/templates/marketing-manager/skills/marketing-manager-getting-started/SKILL.md) |
| marketing-manager-x-browser-video-upload | browser-publishing | `af536432f941abb2ebd917a936cdb06b7d2ce6d0c280ead5cb1a40261f2e2ac9` | [SKILL.md](https://raw.githubusercontent.com/smfworks/grok-bot-templates/d82e405d262cd7e9a56132184f88233a187a7e1a/templates/marketing-manager/skills/marketing-manager-x-browser-video-upload/SKILL.md) |

`browser-publishing` is the X video recipe and the full-length YouTube and Instagram recipe. `supporting` is channel setup, the content and analytics workflow, and the first-run procedure. The same paths on `main` are listed in the allowlist for use after a squash merge, and only when the hash still matches.

Browser publishing skills are recipes for routes the product already permits. They do not sign into X, copy a session, or guarantee that a given account accepts a given video.

## Native export remains blocked

This catalog's convention is a row in the root README whose link opens a published template page. The app creates that page from a packed template. Reported while preparing this template: local SKILL.md files did not register, and UpdateSkill with action write, name, description, and body returned a missing-name or missing-body error even though those fields were sent. The cause is not confirmed. This folder does not claim a skill cap, does not change the app, and does not include a share-import file. The drafted import payload is omitted because it was never a verified app import. With no packed first-run skill, the app's template export cannot publish a share link, so none is listed here.

The evidenced route for a first run without a registered skill is the paste in [onboarding.md](onboarding.md). That is a conversation procedure, not an app template format. This repository has no format the app loads on its own.

## Check the package

From the repository root, with the pinned commit present in the clone:

```bash
python3 templates/marketing-manager/check_template.py
```

After the pinned commit is on the public remote, the same command with `--fetch` downloads each pinned raw URL and checks the bytes. It also requests the `main` URLs: a missing file is expected before merge, and a file that exists must match the hash.

## Privacy

Skills and onboarding are generic. Owners keep brand, account, and campaign details in their own bot. No credential belongs in this folder, in chat, or in a skill body.
