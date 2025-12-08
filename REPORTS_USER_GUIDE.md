# PathSix CRM - Reports User Guide

This guide explains what each report shows you, how it calculates the data, and how to use it effectively to manage your business.

---

## 1. Sales Pipeline Report

**What It Shows:**
- Current leads at each stage of your sales process
- Active projects and their total dollar values
- Overall health of your sales funnel

**How It Works:**
This report looks at all your leads and groups them by status (new, contacted, qualified, lost, converted). It also shows your projects grouped by status (pending, won, lost) along with the total value in each category.

**Data Used:**
- Lead records with their current status
- Project records with status and dollar values
- Date range filters (optional)

**Best Used For:**
- Daily/weekly pipeline reviews
- Identifying bottlenecks in your sales process
- Forecasting which deals are moving forward
- Team meetings to discuss active opportunities

**What to Watch For:**
- Too many leads stuck in one stage (indicates bottleneck)
- Projects sitting in "pending" too long
- Conversion drops between stages

---

## 2. Lead Source Report

**What It Shows:**
- Which marketing channels bring you the most leads
- Conversion rates for each source (how many become customers)
- Which sources deliver your best quality leads

**How It Works:**
The system tracks where each lead came from (website, referral, cold call, email campaign, social media, trade show, advertisement, partner, or other). It then calculates how many leads from each source converted to customers and what percentage that represents.

**Data Used:**
- Lead source field for each lead
- Lead status (to determine conversions)
- Total lead count per source

**Best Used For:**
- Marketing ROI analysis
- Budget allocation decisions (invest more in high-performing sources)
- Identifying which channels to expand or cut
- Sales team training (what works best)

**What to Watch For:**
- Low conversion sources (might need better qualification)
- High-volume but low-quality sources
- Sources with small sample sizes (need more data)

**Important Note:** Leads must have a source assigned for this report to be accurate. Update older leads if needed.

---

## 3. Conversion Rate Report

**What It Shows:**
- Overall percentage of leads that become paying customers
- How long it typically takes to close a deal
- Individual team member performance (admin view)

**How It Works:**
The system counts all leads created in your selected time period, then calculates what percentage reached "converted" status. It also tracks the average number of days between lead creation and conversion.

**Data Used:**
- Total leads created
- Number of converted leads
- Dates of creation and conversion
- Assignment data (for per-user breakdown)

**Best Used For:**
- Setting realistic sales goals
- Identifying top performers
- Spotting team members who need coaching
- Benchmarking your sales process over time

**What to Watch For:**
- Declining conversion rates (process problem?)
- Increasing time-to-convert (deals stalling?)
- Wide variation between team members (training opportunity?)

**Admin Feature:** Admins can see conversion rates broken down by each team member to identify coaching opportunities or celebrate top performers.

---

## 4. Revenue by Client Report

**What It Shows:**
- Your top clients by total project value
- How many projects each client has
- Split between won revenue and pending opportunities

**How It Works:**
The system adds up all project values for each client, separating won projects (done deals) from pending projects (still in progress). Clients are ranked by total value.

**Data Used:**
- All projects linked to each client
- Project values and statuses
- Optional date range to focus on recent activity

**Best Used For:**
- Account management prioritization
- Upselling and cross-selling opportunities
- Recognizing and thanking high-value clients
- Resource allocation decisions

**What to Watch For:**
- Clients with large pending values (need attention)
- One-project clients (upsell opportunity)
- High-value clients with no recent activity (retention risk)

---

## 5. User Activity Report

**What It Shows:**
- How engaged each team member is with the CRM
- Number of interactions, leads, and clients per person
- Overall activity levels across your team

**How It Works:**
The system counts logged interactions, assigned leads, assigned clients, and total activity log entries for each user during your selected time period.

**Data Used:**
- Interaction records created by each user
- Lead and client assignments
- System activity logs
- Date range for the reporting period

**Best Used For:**
- Ensuring CRM adoption across the team
- Identifying inactive users who need training
- Workload balancing
- Performance reviews

**What to Watch For:**
- Zero or very low activity (not using the system)
- Extreme imbalances in workload distribution
- Sudden drops in activity (team member struggling?)

**Admin Only:** This report is only visible to administrators to protect team privacy.

---

## 6. Follow-Up / Inactivity Report

**What It Shows:**
- Tasks and follow-ups that are past due
- Clients with no recent contact (going cold)
- Leads that haven't been touched in a while

**How It Works:**
The system checks all scheduled follow-ups and flags anything past its due date. It also scans your clients and leads, identifying any that haven't had an interaction in the last 30 days (or your custom threshold).

**Data Used:**
- Interaction records with scheduled follow-up dates
- Last interaction date for each client and lead
- Your inactivity threshold setting (default: 30 days)

**Best Used For:**
- Daily task management
- Preventing leads from going cold
- Proactive client relationship management
- Reducing churn risk

**What to Watch For:**
- Long lists of overdue items (need to catch up)
- Valuable clients appearing in the inactive list
- Leads at critical stages going cold

**Pro Tip:** Check this report every morning. Set aside time to handle overdue items first, then reach out to at-risk contacts.

---

## 7. Client Retention Report

**What It Shows:**
- How many clients are active vs. inactive
- Your overall retention rate percentage
- Which clients have recent engagement

**How It Works:**
The system categorizes all your clients by status, then calculates what percentage remain active. It also identifies which active clients have had recent interactions, giving you a "health score" for your client base.

**Data Used:**
- Client status for each record
- Recent interaction history
- Total client counts by status
- Date range for analysis period

**Best Used For:**
- Measuring customer success efforts
- Identifying churn patterns
- Board meetings and investor updates
- Setting retention improvement goals

**What to Watch For:**
- Declining retention rate over time
- Active clients with no recent interactions (retention risk)
- Spikes in "inactive" status changes
- Seasonal patterns in churn

**Industry Benchmark:** Most B2B service businesses aim for 85%+ retention rates annually.

---

## 8. Project Performance Report

**What It Shows:**
- Win/loss record for your projects
- Average project value and duration
- Success rate percentage

**How It Works:**
The system tallies all projects by status (pending, won, lost), calculates total values in each category, and determines your win rate. It also measures average days from project start to completion and average dollar value.

**Data Used:**
- Project statuses and values
- Project start and end dates
- Total project counts
- Date range filters

**Best Used For:**
- Evaluating sales team effectiveness
- Realistic forecasting and goal setting
- Identifying pricing or qualification issues
- Process improvement initiatives

**What to Watch For:**
- Low win rates (qualification problem?)
- Very long average durations (bottlenecks?)
- Wide variation in project values
- Increasing loss rates over time

**Pro Tip:** A 50-60% win rate is typical for well-qualified opportunities. If yours is much lower, you may need tighter qualification criteria.

---

## 9. Upcoming Tasks & Appointments Report

**What It Shows:**
- All scheduled meetings, calls, and follow-ups
- Tasks coming due in the next 30 days (or custom period)
- Who's responsible for each task

**How It Works:**
The system lists all interactions with future follow-up dates, showing how many days until each is due. Tasks are sorted by due date to help you prioritize.

**Data Used:**
- Interaction records with follow-up dates
- Assignment information (who owns each task)
- Optional user filter (admin view)
- Configurable days-ahead window

**Best Used For:**
- Daily and weekly planning
- Team coordination meetings
- Ensuring nothing falls through the cracks
- Workload visibility

**What to Watch For:**
- Uneven task distribution across team
- Clusters of tasks on the same day (too many?)
- Tasks with no assigned owner
- Vague task descriptions that need clarification

**Admin Feature:** Admins can view all team members' upcoming tasks or filter to specific users.

---

## 10. Revenue Forecast Report

**What It Shows:**
- Predicted future revenue based on your current pipeline
- Realistic projections accounting for deal probability
- Context from your lead pipeline

**How It Works:**
The system applies probability weights to your projects based on their status:
- **Pending projects:** 30% weight (historically, 3 out of 10 close)
- **Won projects:** 100% weight (already closed)
- **Lost projects:** 0% weight (not happening)

It multiplies each project's value by its probability, then sums everything to give you a weighted forecast.

**Data Used:**
- All project values and statuses
- Historical win rates (used to set weights)
- Current lead pipeline for context

**Best Used For:**
- Monthly and quarterly revenue planning
- Board presentations and investor updates
- Cash flow projections
- Hiring and resource planning decisions

**What to Watch For:**
- Heavy dependence on a few large deals
- Declining forecast trends
- Mismatch between forecast and actual results (adjust weights)
- Empty pipeline (need more leads!)

**Understanding the Math:**
If you have $100,000 in pending projects, the forecast shows $30,000 (30% of $100K) because history suggests roughly 30% will close. Adjust your expectations accordingly.

**Pro Tip:** Compare your forecast to actual results each quarter. If reality is very different, adjust the weights to better match your business.

---

## General Tips for All Reports

### Date Ranges
Most reports let you filter by date range. Use this to:
- Compare this month vs. last month
- Analyze seasonal trends
- Focus on recent activity vs. historical data
- Generate monthly/quarterly board reports

### Regular Review Schedule
We recommend:
- **Daily:** Follow-Up Report, Upcoming Tasks Report
- **Weekly:** Sales Pipeline Report, User Activity Report (managers)
- **Monthly:** All revenue and performance reports
- **Quarterly:** Retention, Conversion Rate, Lead Source (for strategic decisions)

### Export and Share
Most reports can be exported to spreadsheets or PDF for:
- Team meetings and presentations
- Board updates and investor relations
- Year-end reviews
- Historical record-keeping

### Combining Reports
Get the full picture by viewing multiple reports together:
- **Pipeline + Forecast** = Short-term revenue visibility
- **Lead Source + Conversion Rate** = Marketing effectiveness
- **User Activity + Follow-Ups** = Team accountability check
- **Revenue by Client + Retention** = Account health overview

### Data Quality Matters
These reports are only as good as your data:
- Keep lead sources up to date
- Log all client interactions
- Update project statuses promptly
- Schedule follow-ups consistently
- Assign ownership clearly

---

## Getting Help

**Questions about what data means?**
Ask your CRM administrator or sales manager.

**Technical issues with reports?**
Contact your IT support or the CRM technical team.

**Want a custom report?**
Submit a feature request to your administrator with:
- What question you're trying to answer
- What data you need to see
- How you'd use it in your workflow

---

## Glossary

**Conversion Rate:** Percentage of leads that become paying customers

**Lead Source:** Where a lead originally came from (marketing channel)

**Win Rate:** Percentage of projects that result in won business

**Retention Rate:** Percentage of clients that remain active customers

**Weighted Forecast:** Revenue prediction adjusted for probability of closing

**Pipeline:** Collection of active leads and projects in various stages

**Churn:** When clients become inactive or cancel service

**Follow-Up:** Scheduled next action or contact with a lead/client

**Days to Convert:** Average time from first contact to closed deal
