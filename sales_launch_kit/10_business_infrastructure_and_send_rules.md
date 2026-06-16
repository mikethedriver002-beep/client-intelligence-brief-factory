# Business Infrastructure and Send Rules

This is the operating setup for sending Brief Factory outreach professionally.

## Recommended sender identity

Do not send first outreach from a personal Gmail address or an unrelated brand email.

Use a dedicated business domain and inbox.

Recommended sender:

```text
Display name: Mick | Brief Factory
Email: mick@<brief-factory-domain>
Reply-to: same inbox
```

Backup aliases after the first inbox is working:

```text
hello@<brief-factory-domain>
samples@<brief-factory-domain>
```

Use one real human inbox first. Do not start with a generic no-reply or info-only sender.

## Domain naming guidance

Use the public-facing brand name:

```text
Brief Factory
```

Good domain patterns:

```text
brief-factory.com
trybrieffactory.com
brief-factory.co
clientbrieffactory.com
getbrieffactory.com
```

Pick one available domain and keep the brand simple. Do not use the HSD domain or any unrelated collectibles email.

## Email platform

Recommended first setup:

```text
Google Workspace Business Starter
1 user
Mick | Brief Factory
mick@<domain>
```

Why:

- familiar Gmail interface
- custom business email
- easy Google Drive sharing for samples
- simple enough for a solo founder

## Required DNS/authentication checklist

Before outreach, configure:

```text
MX records for mailbox delivery
SPF
DKIM
DMARC with p=none at first
```

Suggested DMARC starting posture:

```text
v=DMARC1; p=none; rua=mailto:dmarc@<domain>
```

After the domain has history and everything passes, tighten later.

## Warmup and sending limits

Manual founder-led outreach only.

Week 1:

```text
5 emails per day max
same inbox
plain text
no attachments
no mass mail merge
```

Week 2:

```text
10 emails per day max if no deliverability issues
```

Week 3:

```text
15 to 20 emails per day max only if replies are normal and bounce/spam issues are low
```

## Attachment rule

Do not attach files to cold outreach.

First cold email:

```text
No attachment
No ZIP
No PDF
No HTML file
No deck
No calendar link unless they ask
```

Why:

- attachments create friction
- attachments can reduce trust from a cold sender
- prospects have not asked for the sample yet
- the CTA should be one simple reply

## What to send instead

Cold email CTA:

```text
Want me to build a sample for one client niche?
```

If they reply interested, send:

```text
1. a short note
2. one Google Drive folder link or one clean PDF/HTML sample link
3. optional source appendix only if requested
```

## Sample delivery rule

For an interested prospect, send the most polished outputs only:

```text
outreach_ready_sample.html or PDF
agency_sales_sample.html or PDF
weekly_brief.html or PDF
```

Do not send:

```text
delivery_manifest.json
qa_report.json
normalized_items.json
raw ZIP unless they ask
GitHub artifact ZIP
```

Use the raw technical files internally. Prospects should see a clean business sample.

## Output professionalism verdict

The current Brief Factory v0.3.1 packet is professional enough for internal agency review and proof-of-concept sales.

Best files for prospects:

```text
outreach_ready_sample.html
agency_sales_sample.html
weekly_brief.html
```

Files that are not prospect-facing by default:

```text
normalized_items.json
delivery_manifest.json
qa_report.json
delivery_packet.zip
GitHub artifact ZIP
```

## Sender signature

Use a short plain-text signature:

```text
Mick
Brief Factory
White-label client intelligence briefs for agencies
mick@<domain>
```

Do not add a logo, image, long disclaimer, or giant HTML signature for cold outreach.

## First-send checklist

Before sending the first batch:

```text
Domain purchased
Google Workspace inbox created
SPF record passes
DKIM record passes
DMARC record exists
Profile photo optional but helpful
Plain-text signature set
One sample page or Google Drive folder ready
Top 5 prospects verified manually
No attachments in cold email
```

## What good looks like

A good first send is:

```text
short
plain text
from a real person
from a business domain
personalized to the agency
one clear CTA
no attachment
no fake urgency
no big promises
```

## What not to do

Do not:

```text
send from goldencardcollectibles@gmail.com
send from an HSD email
attach a ZIP to a cold email
send 25 emails on day one
use a mass-mailer immediately
claim full automation
claim complete market coverage
hide that this is human-reviewed
```
