# C-Suite Walkthrough Script

## Opening, 0:00-0:45

"Today I will show an AI-powered creative studio for a Southeast Asia fashion retailer.

The issue is not that the marketing team lacks creativity. The issue is that the operating model is too slow for the market.

This retailer needs to run 40-60 campaigns a month across social, display, and email. But the current process still depends on manual briefs, agency turnaround, reviews, and revisions. By the time first drafts come back, a trend window may already be closing.

At the same time, the retailer already owns valuable data: campaign performance, product catalog images, inventory and margin signals, and customer segment profiles. The opportunity is to turn that data into faster, better creative decisions.

This prototype shows what that future workflow can look like."

## Current Opportunity, 0:45-2:00

[Show **1 · Current opportunity**.]

"The first thing to notice is that the marketer does not begin from a blank page.

The app starts with a current opportunity. It looks at what has performed before, which products are ready, and which customer segment has the strongest fit. Then it recommends where the team should focus next.

This matters because campaign planning often starts with opinion: which product should we push, which channel should we use, which audience should we brief for. Here, the starting point is evidence."

[Click **Refresh from data**.]

"I will click **Refresh from data**.

In the prototype, this calls the backend and can make one controlled AI call. In a production environment, this same step could refresh from live media performance, sales, inventory, and customer data.

After the refresh, the app shows that the data was updated just now, and it explains whether the recommendation changed.

For leadership, the value is not only faster content. The value is a better operating rhythm: the business can see what the system is recommending, why it is recommending it, and what signal supports the decision."

## Apply The Direction, 2:00-2:45

[Click **Use this direction**.]

"Now I will use the recommended direction.

The app applies the market, platforms, audience segment, product set, and creative direction into the campaign brief.

This is the first major shift. Instead of waiting for a blank brief to become agency drafts several days later, the marketer starts from a data-backed campaign direction in the same session.

The team is still in control. The system accelerates the work, but it does not remove business judgment."

## Campaign Brief, 2:45-4:00

[Move to **2 · Campaign brief**.]

"Here is the editable campaign brief.

The marketer can change the market, objective, platform mix, audience segment, and product selection. They can also write naturally, the way they would brief a team.

For example: TikTok-first Malaysia launch for Style Enthusiasts. Make it premium, less posed, show product texture and upbeat city energy.

When I use **Refine brief with AI**, the assistant turns that plain-language instruction into structured campaign fields.

The product recommendation area is important. When the audience segment changes, the suggested product category changes too. So the brief is not just using creative preferences. It is connecting the customer segment to the product catalog.

That is where this becomes operationally valuable. It helps the team choose not only what to say, but which products deserve the creative and media investment."

[Click **Create ad previews** or **Refresh ad previews** if needed.]

"Now I will create the ad previews.

Behind this button, the backend analyzes historical performance, segment fit, and catalog readiness, then creates and ranks platform-specific creative options."

## Selected Creative, 4:00-6:00

[Move to **3 · Selected creative**.]

"This is the selected creative recommendation.

It shows the product, platform, customer segment, headline, rationale, and expected impact.

The forecast numbers are not typed manually. They start from historical campaign performance, then adjust for the selected channel, copy style, product, and audience fit.

If the recommendation was refreshed with live AI and then applied, the app can show an **AI-assisted forecast**. That does not mean AI is inventing numbers. It means AI helps interpret and calibrate the forecast, while the backend keeps it within historical guardrails.

This changes the creative review conversation. Instead of asking only, 'Which creative do we like?', the team can ask, 'Which creative is most likely to perform for this audience, on this platform, for this business goal?'"

[Point to **Model presentation**.]

"The marketer also controls the production direction.

They can choose female model, male model, or product only. That choice updates both image and video direction.

For a fashion retailer, this matters. A campaign for modest occasionwear, workwear essentials, or younger style shoppers may need different presentation choices."

[Point to **Image direction** and **Video direction**.]

"The image and video directions are separate because still images and short-form video need different instructions.

The app can use OpenAI GPT Image 2 for image generation today, and it has an AWS Bedrock-ready adapter path for future production use."

## Generate Assets, 6:00-7:15

[Optional: click **Create platform images**.]

"Now I can create platform images.

The prototype is deliberately cost-controlled. It does not generate unlimited variations. It generates assets for the selected platform previews, using the selected products and current direction.

That is an important governance point. The goal is not to flood the organization with AI content. The goal is to use data to decide what deserves production, then create those assets faster."

[Optional: click **Create TikTok video**.]

"The same workflow can extend into short-form video.

For this prototype, the backend is wired to Seedance 2.0 through BytePlus Ark, and the flow can also support a demo-safe cached output. In an AWS production path, this could connect to Amazon Bedrock video generation or Nova Reel, with outputs stored in S3."

## Review And Export, 7:15-8:15

[Move to **4 · Review and export**.]

"The review section shows ranked previews across the selected platforms.

The team can compare ROAS, CTR, expected lift, audience fit, and rationale before committing more production or media spend.

If the brief changes, the app warns the user to refresh previews before exporting. That prevents stale work from being handed off."

[Click **Export**.]

"When the team is ready, I click **Export**.

The export package includes the brief, selected creative, ranked variants, rationale, data-source metadata, and generated asset metadata.

This makes the prototype more than a dashboard. It creates a handoff package that can go to an agency, internal creative team, or activation workflow.

In production, the package could be stored in S3, shared with a presigned URL, and tracked in DynamoDB or Aurora."

## Business Close, 8:15-9:10

"The before state is a three-to-five-day creative cycle, with campaign decisions separated from performance data.

The after state is same-session campaign creation: refreshed recommendations, editable briefs, ranked previews, forecast impact, generated assets, and an exportable launch package.

For a Southeast Asia fashion retailer, the value is speed to trend, better use of media spend, stronger governance, and a clearer link between creative decisions and commercial outcomes.

That is why this matters. It turns retail creative from a slow manual process into an AI-assisted operating model for growth."

## Optional Architecture Appendix, 9:10-10:00

[Use this only if there is time, or if the audience asks how it works.]

"If useful, I can briefly explain how this is built.

The frontend is the creative console for the marketing user.

The backend is a Python service that coordinates the workflow: data loading, performance analysis, recommendation refresh, brief refinement, preview generation, ranking, asset generation, and export.

The AI layer is modular. Recommendation refresh, brief refinement, AI-assisted forecast calibration, image generation, and video generation are separate steps. That means the retailer can control cost, governance, and provider choice.

Today the prototype uses local sample data. In production, campaign data can connect to S3 and Glue, product and customer data can connect to DynamoDB or Aurora, assets can live in S3 and CloudFront, and scheduled refreshes can run through EventBridge or Step Functions.

The key point is that the architecture is designed so the current demo can run simply, while the same workflow can connect to production AWS services later."
