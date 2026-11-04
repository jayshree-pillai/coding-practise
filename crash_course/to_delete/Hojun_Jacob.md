## About me
I’m Jay. I’ve spent over 15 years building systems in financial services, from trading and risk to ML and agentic AI. Currently, I’m working with Mizuho’s AI Centre of Excellence  building AI systems for credit analysis and reporting.

I like trying new ideas, and I’m comfortable taking on a complex problem even when some of the technology is unfamiliar. The research-assistant assignment is a good example: I hadn’t used OpenSearch, PostgreSQL, or Pi before. I learned how they fit together and built a fully functional research assistant, including the evaluation harness and stretch task. That process of learning something new and carrying it through to a working system is something I really enjoy. I don’t get intimidated easily by complexity—I get curious about how to work through it. I think my master’s in financial engineering helped develop that mindset.

## Two aspects of LinqAlpha
**Two aspects of LinqAlpha that intrigue me**While researching LinqAlpha, I found Hojun’s interview on The Fund AI Pod and Jacob’s AWS presentation on YouTube, and worked through their transcripts to understand the thinking behind the product.

**1. Engineering the whole system around the model.**  
Hojun’s discussion of data preparation, financial ontology, agent coordination, and evaluation stood out to me. Jacob made the retrieval piece concrete by explaining how they combine keyword and vector search with financial metadata filters. That’s the kind of engineering I want to work on—connecting the pieces that make AI useful in a financial workflow.

**2. Building skepticism into the research process.**  
Hojun’s “skepticism by design” became tangible through Jacob’s Devil’s Advocate example: start with an investor’s thesis, then find evidence that challenges its assumptions. I find that compelling because the agent helps the investor examine their reasoning while leaving the final judgment with them.

## Why Quit
I’ve learned a lot in my current role, particularly about delivering AI within a large financial institution. But change moves cautiously, and there’s limited room to revisit established approaches or experiment with new ones.

I’m looking for an environment where I can test ideas, challenge assumptions constructively, and move more quickly from an idea to a working solution. The engineering problems Hojun and Jacob described are a big part of why LinqAlpha interests me.


## Q for them
You both emphasized the engineering around the model. Which part of that system is the biggest bottleneck today—and where would you want someone in this role to make the most impact?

I noticed your research publications and your win at SQA’s Alphathon. I’d be excited to contribute to research and competitions like that. Are there opportunities for engineers in this role to get involved?

# LinqAlpha: Detailed Summary of Hojun Choi and Jacob Chanyeol Choi

Prepared from the transcripts and presentation slides shared in this conversation.

This document presents **Hojun first, then Jacob**. Hojun's podcast explains the investor problems, product approach, client workflows, and adoption model. Jacob's AWS presentation provides specific agent demonstrations, retrieval and parsing choices, and infrastructure details.

**Source scope:** The Hojun section uses the pasted podcast transcript. The Jacob section uses the supplied English transcript and four supplied slides; it covers the material provided, rather than claiming to reproduce every part of the original video. Timestamps refer to the supplied Jacob transcript. No additional web research or assumptions about their source code are included.

**Attribution:** This is a paraphrased summary of the supplied material, not a verbatim transcript. Passages explicitly referring to a slide use the uploaded images. Sections 3–4 are editorial synthesis and source-boundary checks. Statements explaining what the material does not establish are also editorial clarifications, not additional statements made by the speakers.

Numbers about clients, productivity, funding, model performance, and renewals are the presenters' claims at the time of their discussions. Unclear transcription and differences between the sources are identified where they affect interpretation.

## Contents

1. Hojun Choi — The Fund AI Pod
2. Jacob Chanyeol Choi — AWS presentation
3. How the two accounts fit together
4. Counts, uncertainties, and implementation details not disclosed
5. Source materials

---

## 1. Hojun Choi — The Fund AI Pod

### Mission: remove friction from investment research

Hojun presents LinqAlpha as infrastructure and research support for investment professionals working across public equities, credit, rates, foreign exchange, and commodities. Its purpose is to help investors connect information, investigate ideas, challenge assumptions, and reach decisions faster. He frames the mission around removing research friction and supporting deeper, independent thinking. The investor retains the final judgment.

He describes a recurring problem: research is scattered across broker emails, newsletters, years of internal notes, market-data services, and many applications. He gives examples of decades of accumulated research and users moving among 30–40 applications. Analysts spend substantial effort finding and reconciling information before they can investigate its implications. LinqAlpha aims to make those sources usable by agents that support the research process.

His background account includes investment banking at Goldman Sachs, joining with a team of PhDs, and raising approximately $6.6 million after retrieval-benchmark success. These are his account of the company’s development. The transcript garbles some names and technical terms, so it should not establish precise details where the wording is unclear.

### Two foundational components, three categories of work

Early in the interview, Hojun describes **two foundational components**:

1. **A centralized intelligence layer:** process fragmented information so agents can find, understand, and combine it. Later comments clarify that this can involve connecting existing systems rather than physically moving everything into a new repository.
2. **Specialized agents working together:** different agents contribute different capabilities, including numerical analysis, social-media interpretation, and criticism of an investment argument.

He separately identifies **three categories of agent use cases**:

| Category | What it does | His examples |
|---|---|---|
| **Monitoring** | Watches for changes on a schedule or in response to events. | Daily or weekly monitoring, price movements, mentions, filings, earnings transcripts, and central-bank minutes across hundreds of instruments. |
| **Synthesis and aggregation** | Combines overlapping information and identifies what matters. | Comparing broker responses to earnings, finding an outlying view, producing company research, and extracting signals from social commentary. |
| **Prediction** | Uses historical precedents and quantitative analysis to investigate possible directions and changing signals. | Studying current movements against earlier situations and developing probabilistic implications. |

These are different classifications: the two components describe the foundation; the three categories describe work performed with it. The categories are not a mandatory sequential pipeline. Prediction is presented as useful analysis under uncertainty, not guaranteed forecasting accuracy.

### The ontology problem: connecting financial meaning

Hojun argues that public-market research requires continuously managing interconnected knowledge. His example is a question about Chinese property-market distress and its implications for an equity portfolio. Relevant research might involve credit ratings, distress, macroeconomic conditions, central-bank policy, equity identifiers, and portfolio weights.

He contrasts this with private-market workflows that he characterizes as extracting information from documents in a data room, such as clauses or accounting details. His claimed differentiation is handling a growing network of public-market information and its implications across assets. This is his positioning argument, not an independently verified comparison of competing products.

Hojun describes financial ontology in terms of extracting entities and mapping relationships. He says unstructured documents often lack usable identifiers, and that extracting identifiers and other metadata helps agents navigate the information.

He says ingestion extracts more than **100 metadata fields**, including identifiers, analyst names, target prices, sectors, and asset classes. He also emphasizes processing HTML, PDFs, emails, charts, and tables. A model can misread a complex chart or collapse table rows and columns, so data preparation matters before reasoning begins.

The interview does not specify an ontology schema, graph database, search implementation, or exact extraction-validation process. Relationships indicate what to investigate; they do not by themselves establish a causal effect on a portfolio.

### Why the system around the model matters

Hojun says LinqAlpha generally uses advanced models from AI labs rather than building an equivalent frontier reasoning model itself. He attributes much of overall performance to ingestion, financial relationships, orchestration, and evaluation. His estimate that the model contributes only 30–40% of performance is a framing claim; the interview supplies no measurement behind that decomposition.

His Formula One analogy makes the point intuitive: the engine matters, but the performance of the complete car also depends on the surrounding systems. In his account, choosing a strong foundation model is one part of building a useful financial AI product.

For multiagent design, he names concrete decisions: when to retain a central planner, when to delegate to sub-planners, how to assign responsibilities, and how to minimize duplicated work. Different roles may specialize in statistics, social-media analysis, or challenging an argument.

This explains what he means by proprietary architecture, but it does not reveal the actual routing algorithm, inter-agent contracts, stopping rules, or model assigned to every role. Nor does it imply that every question invokes every agent.

### MCP and the problem of selecting context

Hojun describes MCP-native architecture as increasingly important for accessing external capabilities and information. However, more connections can also introduce more irrelevant material into the model’s context. He therefore emphasizes orchestration and managing the balance between useful information and noise.

**Editorial clarification:** These comments distinguish preparing information, connecting tools and sources, and selecting useful context. This is a way of organizing his explanation, not a three-part architecture he explicitly names. The transcript does not say that every internal operation uses MCP or explain a particular context-selection algorithm.

### Quantitative work: execute calculations, verify the inputs

He argues against asking a text model to perform numerical calculations purely through generated prose. Instead, coding agents can write and execute Python or SQL against structured data, then combine the results with qualitative research. An orchestrator brings the contributions together.

One illustrative exercise counts management references to generative AI and compares them with capital expenditure—a “talk-to-action” comparison. He also mentions regression and multivariate analysis that connect numerical findings to an investment narrative.

Although he speaks strongly about preventing numerical hallucination, he acknowledges that an LLM writing Python or SQL can pull the wrong numbers. He says appropriate context engineering helps it retrieve the relevant numbers and combine them with qualitative analysis. The transcript does not describe an interface for inspecting generated code or calculation traces.

### Two evaluation buckets

Hojun separates evaluation into two kinds of questions:

| Bucket | Example | What must be assessed |
|---|---|---|
| **Factual, or “trivial”** | NVIDIA’s revenue last year. | Cross-check against fundamental datasets; Hojun says these questions have a ground truth. |
| **Judgment-based, or “nontrivial”** | Whether the market faces GPU oversupply. | Assess the quality of the evidence, structure, and reasoning when no single definitive answer exists. |

He compares the second category to grading an essay. He treats source traceability as established industry practice and says evaluating qualitative answers requires going beyond factual ground truth to assess whether a response is structured, logical, and persuasive.

He says LinqAlpha also helps clients evaluate these responses. The interview does not disclose a complete rubric, scoring system, or production acceptance threshold.

### Skepticism, model bias, and alpha decay

The interviewer raises a crowding concern: if many funds use the same platform, could they receive similar answers and make similar decisions? The transcript’s “alpha degeneration” refers to the possible erosion of an investment advantage as more participants act on it. This is a concern about convergence and crowding, rather than a question about whether private client data is mixed.

Hojun’s response is that the platform supports investors’ own views, helps challenge them, and expands their research capacity. He also says models can exhibit sector, company-size, and momentum-versus-contrarian biases, referencing research he calls “Your AI, Not Your View.” Using multiple models and building in **“skepticism by design”** are presented as ways to broaden and challenge analysis.

His argument explains the intended differentiation between clients. It does not prove that shared tools or models cannot contribute to convergent conclusions.

### Reusable capabilities and client-specific workflows

Hojun says the company has built more than **30 agents**, broadly covering the three use-case categories. He describes reusable “LEGO blocks” that can be combined into tools tailored to a client’s requirements.

Customization includes investment style, preferred research questions, sector-specific metrics, reporting format, and feedback. Even an earnings summary can mean different things to different analysts: one wants particular operational metrics, while another emphasizes thematic developments.

He envisions agents adapting through instructions, feedback, memory, and context. He does not say that each client receives a newly trained model. He also says understanding and designing a requested workflow typically takes two to three weeks; that is not a stated guarantee for complete production deployment.

### Infrastructure, onboarding, and deployment

Asked which agents a new fund should adopt first, Hojun prioritizes the underlying infrastructure. Agents are less useful when relevant information is inaccessible or fragmented. He emphasizes access across regions, asset classes, and structured and unstructured datasets, with an architecture that can incorporate new capabilities.

For an existing manager, onboarding begins by understanding its systems, storage, data flows, portfolio tracking, and risk information. LinqAlpha then connects to relevant sources and identifies workflows worth supporting. Cloud storage is preferred, but he explicitly avoids framing onboarding as compulsory migration or wholesale process replacement.

He mentions Microsoft tools such as Outlook, SharePoint, OneNote, and OneDrive. A representative question is reconstructing why the firm shorted Adobe in an earlier quarter and comparing its thesis with market consensus.

Deployment options discussed include public cloud, virtual private cloud, and on-premises arrangements. He describes work with Microsoft and other hyperscalers around connectivity, encryption, and enterprise requirements, without specifying detailed security controls or deployment designs.

### Client stories and illustrative scenarios

The interview mixes reported client use with examples of possible analysis:

- **Meeting support—reported use:** an agent uses a virtual computer to attend, translate, transcribe, summarize, and propose follow-up work. Overseas calls, including a 3 a.m. Japan call, illustrate the value. He says some clients use the capability more than 100 times monthly.
- **Social-media research—reported use:** investors examine sentiment and underlying comments, with Starbucks unionization and Chipotle portion concerns as examples. Verbatim evidence accompanies interpretation.
- **Broker-note comparison—illustrative scenario:** after earnings, synthesize ten similar broker emails and identify the meaningful outlier.
- **Cross-asset implications—illustrative scenario:** investigate how Japanese elections could affect rates, currencies, and portfolio exposures.
- **Faster hypothesis testing—claimed benefit:** he contrasts hours of traditional work with testing five to ten hypotheses in roughly 30–60 minutes using agents. No independent benchmark is supplied.

### Adoption, delivery models, and the future

Hojun describes a spectrum from skeptical investors, concerned about losing independent thinking, to users who expect a challenging research partner. Most organizations sit between these extremes. He says training and a structured adoption process matter, and describes users concluding that AI does not work after unsuccessful early attempts. He mentions both firms using AI-usage leaderboards and firms distributing tools with limited guidance.

LinqAlpha has two delivery approaches. Smaller managers without core engineering teams can use a web-based terminal. Larger institutions can work with LinqAlpha alongside their engineering teams to build proprietary tools. He presents the latter as allowing clients to retain ownership while using shared capabilities to accelerate development; exact contractual terms are not provided.

He also discusses managing pilot costs while existing subscriptions remain in place. His “a la carte” data argument is that clients may be able to purchase the fundamentals, estimates, prices, or ownership information they need without paying for a much broader bundle of unused capabilities. He presents this as a way to manage initial double spending and explore longer-term integration choices, not as a requirement to replace every existing service.

His future vision centers on bridging discretionary research and systematic analysis. Coding agents make quantitative methods more accessible, while connected information supports broader cross-asset investigation. The investor can explore more hypotheses and perspectives, but remains responsible for the ultimate decision.

## 2. Jacob Chanyeol Choi — AWS presentation

### 2.1. Starting point: build from financial data toward useful research agents

Jacob explains how LinqAlpha turns varied financial information into searchable evidence and then into investment-research workflows. His two detailed examples are the **Company Screener** and **Devil’s Advocate** agents. He later introduces **Primer** and **Stock Catalyst** to illustrate a broader research process.

He describes an approximately two-year development journey, initially working with relatively small hedge funds whose decision-making structures and openness to public cloud enabled rapid iteration. He says the product subsequently expanded to asset managers and investment banks. The supplied translation marks the early clients’ assets-under-management wording and a bank-client name as unclear; those details should remain qualified.

His underlying problem is the breadth of information analysts must examine: financial metrics, filings, earnings announcements, brokerage reports, internal memos, emails, expert discussions, and social media. He cites Labubu-related TikTok interest as an example of alternative information attracting attention before subsequent stock-market movement. This illustrates his interest in broader information sources, without establishing a general predictive rule.

### 2.2. The three technical layers in the presentation

**Slide evidence:** The uploaded architecture slide, whose title translates as **“From Data to Building Agents,”** organizes the platform as follows:

| Layer | What the slide contains | Meaning in the presentation |
|---|---|---|
| **Data** | Structured data, unstructured data, alternative data, data integration, and virtual data rooms | The different information sources available to research workflows. |
| **RAG + LLM** | Parsing and processing, embedding, retrieval, reranking, contextual integration, and generation | The preparation, search, and generation capabilities underneath the visible product. |
| **Agents** | Specialized financial AI agents | Research tasks built using those underlying capabilities. |

The diagram names **reranking** and **contextual integration**, but the supplied material does not specify their algorithms. Its generation component is labeled “Single LLM”; this does not establish that the whole platform always uses one model. These are architectural layers, whereas Hojun’s monitoring, synthesis, and prediction buckets classify investor use cases.

### 2.3. Company Screener: identify companies worth investigating

**Relevant passages: 10:15–17:49.**

Jacob starts with an investor responding to an event, such as a change in U.S.–China tariff policy. The investor may need to assess hundreds or thousands of companies to identify different degrees of exposure and develop investment ideas.

The demonstration has **two distinct filtering stages**:

1. **Narrow the company universe using explicit criteria.** Users select sectors and market-capitalization thresholds. His example selects software and internet companies and discusses excluding very small companies if their volatility is unsuitable.
2. **Ask an analytical question about each remaining company.** The system examines evidence and produces answers that can support further filtering. The demonstrated questions concern a company’s relationship to a regulation and whether that relationship affects its main revenue drivers. Answers can be presented as yes/no results.

The initial sector or market-cap filter is different from the subsequent evidence-based judgment about a company. It would be inaccurate to describe the entire workflow as an LLM guessing search filters.

Supporting documents accompany the answers. Investors can investigate further through earnings-call transcripts or full regulatory filings. Jacob reports that work previously taking more than two hours per stock has been reduced to under twenty minutes in repeated use. He connects that saving to broader coverage and more time for analysis; the talk does not supply a controlled study of research quality or investment returns.

### 2.4. Why OpenSearch and how retrieval supports the Screener

**Relevant passages: 12:06–14:52 and 16:52–17:49.**

Jacob describes starting with Pinecone, trying alternatives including Milvus and Qdrant, and eventually selecting **OpenSearch**. One additional product name is unclear in the supplied transcript.

His stated reasons include:

- **Full-text search and text processing**, including stemming, for financial documents.
- **Multilingual tokenization**, supporting research across countries and languages.
- **Complex metadata filtering**, using information extracted from documents in advance.
- **Hybrid retrieval**, combining keyword matching with vector-based semantic similarity.

His metadata example is a request for reports by a particular analyst at a particular bank that contain a buy recommendation. He also states that their use case can accommodate more than **5,000 metadata attributes**. The scope and counting method are unspecified; this is not evidence that every document contains thousands of populated fields.

In the backend description, financial data is embedded **in advance**, stored or indexed in OpenSearch, and later retrieved to support responses. **Amazon Bedrock** supplies generation and reasoning, while services including S3 and EC2 support the wider implementation.

He identifies **Claude 3.7 Sonnet through Bedrock** as the selected model for the discussed reasoning task. Selection considered criteria developed by a former financial analyst, plus **time to first token** and **formatting-error rate**. Those criteria combine domain usefulness with operational behavior; the precise rubric and comparative scores are not provided.

### 2.5. Devil’s Advocate: test an investor’s assumptions

**Relevant passages: 17:56–21:02.**

The second detailed agent addresses **confirmation bias**. Jacob describes investors becoming attached to a company after studying it extensively, including institutional investors who may find it difficult to challenge their accumulated conviction.

The analyst supplies an investment thesis, potentially five to ten pages, and relevant documents. Jacob gives examples of uploading 500 or 1,000 expert interviews that an analyst lacks time to read individually. The system examines relevant information from interviews, filings, research reports, and other material, then presents **counterarguments with citations**.

For a thesis that generative-AI adoption will raise a company’s revenue, possible objections include an unproven monetization model or customers resisting higher prices. The agent gives the analyst opposing evidence to consider when assessing whether their assumptions might be mistaken.

Jacob describes this as enabling more traceable investment validation and better preparation for investment-committee discussions. He reports several hours of weekly time savings, but the exact number is explicitly unclear in the supplied translation.

### 2.6. The smaller agents inside Devil’s Advocate

**Relevant passages: 21:09–25:03.**

| Internal component | Responsibility described |
|---|---|
| **Parsing Agent** | Extract information from uploaded documents. |
| **Retriever Agent** | Find evidence relevant to the investment thesis. |
| **Synthesizer Agent** | Organize retrieved material into a clear report for the analyst. |

Here, **“agent” describes two levels**: Devil’s Advocate is the workflow the investor uses, while parsing, retrieval, and synthesis are components within that workflow. Their labels alone do not establish exactly how independently or autonomously each component operates.

For parsing, Jacob names **Amazon Textract** and **Claude 3.7 Sonnet through Bedrock as a vision-language model**. Financial evidence includes tables, charts, and images, so extraction must retain relationships between values and their context. His example concerns a company’s share price at a particular time and changes in analysts’ price targets. Claude Sonnet is also mentioned for retrieval and synthesis, but the model version in that passage is garbled.

The described architecture is:

1. Store the investor’s thesis.
2. Upload documents to **S3**.
3. Parse them and store extracted information.
4. Use **OpenSearch and RDS** to retrieve relevant material and perform repeated validation.
5. Use **Bedrock** to produce the counterargument report.

The talk mentions parallel document processing and handling lengthy inputs. It does not explain the validation loop’s scoring criteria or stopping rule, the database tables, or the division of responsibilities between OpenSearch and RDS. **RDS is named without a database engine; PostgreSQL cannot be inferred.**

### 2.7. Primer, Stock Catalyst, and a connected research workflow

**Relevant passages: 25:08–29:40.**

Jacob describes expanding the product toward analytical reports, longer historical coverage, and different workflows for equities, credit, commodities, and fixed income.

His end-to-end example introduces four investor-facing agents:

| Step | Agent | Intended contribution |
|---|---|---|
| 1 | **Company Screener** | Narrow a broad universe into companies worth researching. |
| 2 | **Primer** | Develop an initial understanding of a company’s business, fundamentals, and revenue drivers. |
| 3 | **Stock Catalyst** | Investigate relevant events, historical patterns, and possible triggers of stock-price movements. |
| 4 | **Devil’s Advocate** | Challenge the resulting investment hypotheses against documentary evidence. |

The Primer discussion emphasizes smaller or less-covered companies, where available research may be limited or outdated. The spoken example describes creating an up-to-date research report; the slide’s Korean caption also emphasizes quickly summarizing lengthy research material.

For Stock Catalyst, Jacob proposes examining how a company and its stock responded to a comparable tariff event in the past. The supplied slide visibly uses Adobe, although the company name is unclear in the transcript. Historical comparison supplies material for investigation; it does not establish that the next outcome will repeat the past.

This is an **illustrated research sequence**, not proof that every question automatically runs all four agents.

### 2.8. AWS as the operating foundation

**Relevant passages: 29:40–31:11 and the AWS infrastructure slide.**

Jacob describes combining Bedrock, OpenSearch, Textract, S3, RDS, and compute services within AWS. He argues that integrating components in one cloud reduces the operational dependencies involved in coordinating separate platforms. That is his architectural rationale, rather than a demonstrated guarantee of reliability.

The accompanying slide emphasizes five benefits: an integrated AI-and-data stack, expansion during peak workloads, interoperability, flexibility to replace models or upgrade embeddings, and support for security and regulatory requirements. Earnings season is his concrete example of continuous document arrivals and heightened demand. The supplied material does not identify specific queues, autoscaling policies, failure-recovery mechanisms, or security controls.

### 2.9. The “superintelligent investor” vision

**Slide evidence:** The final uploaded slide combines **systematic implementation** with **discretionary insight**. Its intended division of contributions is:

- **Systematic implementation:** rapidly test ideas and hypotheses, monitor and analyze large amounts of data, and maintain quality as research coverage expands.
- **Discretionary insight:** apply experience and expertise, interpret ambiguity and unusual signals, and develop investment ideas using intuition and judgment.
- **Supporting foundation:** reliable AWS infrastructure and services.

The slide’s overarching message is to combine scalability and precision with human creativity and conviction. Jacob explicitly leaves the final investment decision with the person. His “superintelligent investor” describes the intended enhancement of that person’s capabilities.

### 2.10. Counts and claims to retain with their qualifications

Jacob reports approximately **170 institutional clients** and **100% annual-contract renewal**, without providing measurement details in this excerpt. These remain presenter-reported figures.

At 26:32–27:04, he says **more than 50 agents have been developed and are being tested**. The supplied architecture slide displays **100+ specialized financial AI agents**. Neither source explains how those counts relate to each other or to Hojun’s 30+ figure. They should not be silently reconciled into a single production inventory.

## 3. How the two accounts fit together

**Editorial synthesis:** This section connects statements from the supplied transcripts and slides. It is our interpretation of how the accounts relate, not a further presentation or a description of undisclosed implementation.

### 3.1 Four different ways of describing the system

The speakers use the word **agent** at different levels. Their classifications should not be combined into a single inventory.

| Perspective | What it describes | Examples in the supplied material |
|---|---|---|
| Investor needs | Categories of work the product supports | Hojun's monitoring, synthesis and aggregation, and prediction |
| User-facing workflows | Research tasks an investor can ask the product to perform | Company Screener, Primer, Stock Catalyst, Devil's Advocate; Hojun also describes meeting, social-media, and quantitative-analysis capabilities |
| Internal components | Parts that carry out a larger workflow | Jacob's Parsing, Retriever, and Synthesizer agents inside Devil's Advocate |
| Technical architecture | The underlying layers supporting the product | Data layer, RAG + LLM layer, agent layer |

The three use-case buckets are not three mandatory sequential steps. The four-agent research sequence is an illustrated workflow, not evidence that every request runs all four agents. Calling a component an agent also does not reveal exactly how independently it plans or acts.

### 3.2 The strongest connections between the talks

| Hojun's explanation | Jacob's concrete example or implementation detail |
|---|---|
| Financial information must be prepared and made navigable before agents can use it effectively. | Embeddings generated in advance, metadata filtering, and OpenSearch hybrid retrieval. |
| Financial meaning must survive ingestion, including difficult charts and tables. | Textract and Claude vision-based parsing; associating chart values and analyst targets with the correct point in time. |
| Agents should challenge assumptions through skepticism by design. | Devil's Advocate takes an investment thesis and produces counterarguments with supporting citations. |
| Specialized capabilities can be combined into bespoke client workflows. | Internal parsing, retrieval, and synthesis components; an illustrated sequence from company screening to thesis validation. These illustrate modularity without exposing the exact shared code. |
| Quality depends on the system around the foundation model. | Specific retrieval, model-selection, parsing, and infrastructure choices, with analyst criteria and operational metrics. |
| AI should help investors investigate more hypotheses and retain their own judgment. | Company screening, company research, historical catalyst analysis, and an explicit final vision of a human investor supported by AI. |

Together, the accounts describe a reusable research foundation serving different investment tasks. This is a synthesis of the supplied materials, not a claim that all product workflows share an identical implementation.

### 3.3 What "agent-native" means in these discussions

Hojun's emphasis is on infrastructure that makes agents useful: access to existing data sources, prepared information, suitable tools, context management, and ways for specialized capabilities to work together. MCP addresses part of the tool-access problem; it does not by itself determine what information is relevant or how a workflow should reason.

Jacob supplies concrete examples of this foundation on AWS. His workflow descriptions show how document preparation, retrieval, and generation support the research tasks exposed to an investor. He explicitly says they design different data workflows and decision trees for different investment strategies. Hojun separately discusses client preferences, reporting formats, instructions, and feedback. The talks do not show the exact code-versus-configuration boundary.

### 3.4 The shared human role

Both speakers leave the final investment decision with the person. The system is intended to expand how much evidence an investor can examine, how many hypotheses they can test, and how readily they can challenge assumptions. **An implication of this approach** is that an investor may strengthen, revise, or abandon a thesis after reviewing opposing evidence; that is our interpretation of the workflow, not wording attributed to either speaker.

Hojun describes this as reducing research friction and supporting independent thinking. Jacob's closing slide combines systematic implementation with discretionary insight under the label **superintelligent investor**. This is their product vision, not evidence of guaranteed investment performance.

## 4. Counts, uncertainties, and implementation details not disclosed

**Editorial source audit:** This section records differences between the supplied sources and limits on what they establish. It does not add claims about LinqAlpha's actual implementation.

### 4.1 Figures that should not be silently reconciled

| Topic | What the shared sources say | What can safely be concluded |
|---|---|---|
| Agent counts | Hojun: more than 30. Jacob's speech: more than 50 developed and being tested. Jacob's architecture slide reads: "+ 100 Specialized Financial AI Agent". | The sources use different figures and may refer to different scopes or stages. They do not explain the discrepancy or establish a growth timeline. |
| Metadata counts | Hojun describes extracting more than 100 metadata fields. Jacob says OpenSearch can accommodate more than 5,000 metadata attributes for their financial use cases. | The definitions and scope of the counts are unspecified. Neither establishes that every document has all those fields populated. |
| Model contribution | Hojun estimates that the model accounts for 30–40% of overall system performance. | This expresses his emphasis on surrounding engineering; the transcript does not provide a measured decomposition. |
| Clients and renewals | Jacob reports approximately 170 institutional clients and a 100% renewal rate on annual contracts. | These are presentation claims without a disclosed denominator, observation period, or measurement method. |
| Productivity | Hojun discusses testing five to ten hypotheses in 30–60 minutes and frequent meeting-agent use. Jacob reports screening research falling from more than two hours per stock to under 20 minutes. | These are reported experiences and examples, not universal benchmarks. Jacob's weekly hours-saved figure is explicitly unclear in the supplied transcript. |

### 4.2 Implementation boundaries

The presentations do **not** establish:

- A particular orchestration framework, exact planner algorithm, agent communication protocol, or formal stopping rule.
- The engine behind **RDS**, its table schemas, canonical records, or the identifiers linking relational data to OpenSearch. RDS should not be relabeled PostgreSQL based on this material.
- A specific graph database or ontology schema. Hojun's discussion establishes the importance of entities and relationships, not the storage implementation.
- The exact retrieval-fusion algorithm, reranker, contextual-integration method, or filtering logic used for every query.
- How parsing completeness is checked, how missing chart or table information is detected, or what all recovery paths are.
- Whether evaluation is offline, performed during each request, or both; the exact analyst rubric, judge setup, acceptance thresholds, and deployment gates are not supplied.
- Detailed queues, concurrency settings, autoscaling policies, SLAs, tenant boundaries, or controls preventing cross-client retrieval.
- That every agent uses the same model or that a model named in one presentation remains the current choice throughout the product.

### 4.3 Two distinctions worth preserving

**Investment convergence versus data isolation:** The podcast's herd-mentality question asks whether many funds using the platform will reach similar investment decisions. Hojun answers in terms of individual theses, skepticism, model bias, and investor judgment. That answer does not describe technical controls preventing one client's confidential information from reaching another client.

**Executable code versus correct analysis:** Hojun acknowledges that an LLM writing Python or SQL can pull the wrong numbers. The distinction drawn here is that successful execution alone does not resolve the data-selection error he describes. The transcript does not list specific failures involving joins, periods, or units, or describe a code-inspection feature.

## 5. Source materials

The summaries above are grounded in the materials supplied by the user. Public links below identify the recordings; they are not additional sources used to fill gaps in the transcripts.

1. **Hojun Choi:** The full podcast text pasted into this conversation, from [The Fund AI Pod — EP10](https://www.listennotes.com/podcasts/the-fund-ai-pod/ep10-hojun-choi-co-founder-h14gsQYC_NE/). The supplied text contains obvious transcription errors; unclear proper names and missing words have not been treated as verified facts.
2. **Jacob Chanyeol Choi:** [Supplied English transcript — Pasted markdown.md](https://chatgpt.com/library?file_id=libfile_7ae1fe5a46ac81919809a7c5c6ed83d9&account_id=personal), associated with the [AWS Korea presentation](https://www.youtube.com/watch?v=jKBqh3hnYHo). Bracketed uncertainty in the supplied translation is preserved in the interpretation.
3. **Architecture slide:** [From data to agents](https://chatgpt.com/library?file_id=libfile_9743c231370881919703cc2a96b89b40&account_id=personal).
4. **Workflow slide:** [Company Screener, Primer, Stock Catalyst, and Devil's Advocate](https://chatgpt.com/library?file_id=libfile_8d6ed26944d48191af20849e2ef4037f&account_id=personal).
5. **Infrastructure slide:** [AWS support for multi-agent systems](https://chatgpt.com/library?file_id=libfile_8870651a9b3081918d3bc502df128c2a&account_id=personal).
6. **Vision slide:** [The superintelligent investor](https://chatgpt.com/library?file_id=libfile_a396cff657c8819181571ce30c5842ef&account_id=personal).
