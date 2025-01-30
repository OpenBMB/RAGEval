from dataclasses import dataclass
from typing import List
from openai import OpenAI
from typing import List, Dict
import json
import re
import time
import os

KEY_PROMPT_ZH = """
在这个任务中你会获得问题，生成回答，以及标准回答要点三个信息，找到与标准回答要点描述最相关的生成回答中的子片段，称为生成回答的可对比片段。分析生成回答的可对比片段中是否存在与标准回答要点相关且一致或者不相关或者矛盾的情况，并给出相关简要说明，最后给出结论。
结论只能输出：[[[Relevant]]] 或者 [[[Irrelevant]]] 或者 [[[Wrong]]]，分别表示 "相关且一致" 或者 "不相关" 或者 "错误"。以下是对着三种结论的详细定义：
[[[Relevant]]]代表生成回答的对比片段中与标准回答要点描述相关且一致，注意仅需要对回答该问题的必要信息一致即可，不需要所有细节，我们确保每个标准回答要点整体上是必要的，不过中间可能有些细节对回答问题不是一定要包含的，判断的时候仅需判断最重要的信息包含即可作为与回答要点Relevant；
[[[Irrelevant]]]代表生成回答的对比片段中没有包含或者没有涉及到与标准回答要点的相关部分, 或者生成答案中明确提到相关细节信息不足，但是key中相关内容有确定的答案；
[[[Wrong]]]表示生成的回答片段在重大问题上不符合标准答案中描述的要点。当生成的回答说明某部分没有足够的信息进行回答时，这将被视为‘无关’而不是‘错误’，只有当生成的回答对某个问题给出了具体但不正确的答案时，才会被视为‘wrong’。在不影响问题回答的情况下，某些细节上的不足不应被视为'wrong'，而应视为'irrelevant'。”

每次请求只会有一个要点，所以你只能输出一个[[[Relevant]]]或者[[[Irrelevant]]]或者[[[Wrong]]]，而不能输出多个。请综合理解问题，并分析生成回答可对比片段是否与标准回答要点中的信息 相关且一致 或者 不相关 或者 矛盾。在要点评估中简要说明分析，最后给出结论。

例子1：
问题：财富管理手续费收入的现状及未来展望是怎样的？
生成回答：前三季度，该行实现财富管理手续费收入为51.05亿元，同比下降20.7%。这一下降主要是由于主动压降非标类产品规模以及证券市场波动导致的基金销量下滑等因素所致。为了应对这种情况，该行计划持续升级产品、队伍、专业及科技能力。具体措施包括提升资产优选与产品甄别能力，丰富、优化产品货架，持续加强专业化队伍建设，并着力提升队伍专业技能及中台赋能水平，以增强队伍内生发展能力。未来展望包括通过这些措施实现更加稳健、更高质量的发展，以应对财富管理手续费收入下滑的挑战。
标准回答要点：
财富管理手续费收入的现状：前三季度收入同比下降21.6%。
要点评估：
分析生成回答的可对比片段："前三季度，该行实现财富管理手续费收入为51.05亿元，同比下降20.7%"。相关简要说明：生成回答的可对比片段中提到“财富管理手续费收入为51.05亿元，同比下降20.7%”。标准回答要点提到“财富管理手续费收入的现状：前三季度收入同比下降21.6%”。二者都在描述同比下降的情况，但具体下降百分比有所不同。结论：[[[Wrong]]]

例子2：
问题：从最新的财报数据中，电子行业的表现有哪些显著特点和趋势？
生成回答：
电子行业的显著特点和趋势包括：市场需求稳步增长，尤其是消费电子产品和半导体行业；技术创新不断推进，5G和物联网相关产品成为增长亮点；企业盈利能力显著提高，毛利率普遍上升；供应链压力有所缓解，原材料价格趋稳；但资本开支并未增加，目前还处于观望阶段，因此一些行业非头部企业在并未将大量新技术应用投入市场。
标准回答要点：
资本开支增加，重点在技术研发和产能扩张。
要点评估：
生成回答的可对比片段是：“但资本开支并未增加，目前还处于观望阶段，因此一些行业非头部企业在并未将大量新技术应用投入市场”。分析：标准回答要点强调资本开支增加，重点在技术研发和产能扩张，而生成回答提到资本开支并未增加，目前还处于观望阶段。因此，生成回答与标准回答要点存在矛盾。结论：[[[Wrong]]]

例子3：
问题：财富管理手续费收入的现状及未来展望是怎样的？
生成回答：前三季度，该行实现财富管理手续费收入为51.05亿元，同比下降20.7%。这一下降主要是由于主动压降非标类产品规模以及证券市场波动导致的基金销量下滑等因素所致。为了应对这种情况，该行计划持续升级产品、队伍、专业及科技能力。具体措施包括提升资产优选与产品甄别能力，丰富、优化产品货架，持续加强专业化队伍建设，并着力提升队伍专业技能及中台赋能水平，以增强队伍内生发展能力。未来展望包括通过这些措施实现更加稳健、更高质量的发展，以应对财富管理手续费收入下滑的挑战。
标准回答要点：
财富管理手续费收入的现状：前三季度收入为51.05亿元。
要点评估：
生成回答的可对比片段是：“前三季度，该行实现财富管理手续费收入为51.05亿元，同比下降20.7%”。分析：生成回答的这部分明确提到了“前三季度收入为51.05亿元”，与标准回答要点描述完全一致。结论：[[[Relevant]]]

例子4：
问题：从2022年年报和2023年一季报中，医药板块表现出哪些关键趋势和特点？
生成回答：
医药板块表现出的关键趋势和特点包括：分化行情、估值内部分化、板块复盘、医药基金仓位回归、原料药化药、中药、医疗设备、C钞等盈利能力回升，负债率分析负债率几个都是降低的，资本开支的强度趋缓。
标准回答要点：
化药、中药、医疗耗材以及诊断服务等细分领域经历了一轮估值扩张。
要点评估：
生成回答的可对比片段：“原料药化药、中药、医疗设备、C钞等盈利能力回升”。标准回答要点：“化药、中药、医疗耗材以及诊断服务等细分领域经历了一轮估值扩张”。分析：生成回答提到的“原料药化药、中药、医疗设备”等领域与标准回答要点提到的“化药、中药”部分一致。生成回答提到“盈利能力回升”，而标准回答要点提到的是“估值扩张”，这两者都是积极的表现，但具体方向不同，一个是盈利，一个是估值。生成回答未提及“医疗耗材”和“诊断服务”，但其提到的“医疗设备”与“医疗耗材”有一定相关性。结论：[[[Irrelevant]]]

例子5：
问题：从最新的财报数据中，电子行业的表现有哪些显著特点和趋势？
生成回答：
电子行业的显著特点和趋势包括：市场需求稳步增长，尤其是消费电子产品和半导体行业；技术创新不断推进，5G和物联网相关产品成为增长亮点；企业盈利能力显著提高，毛利率普遍上升；供应链压力有所缓解，原材料价格趋稳；但资本开支并未增加，目前还处于观望阶段，因此一些行业非头部企业在并未将大量新技术应用投入市场。
标准回答要点：
企业盈利能力提高，毛利率上升，进而供应链压力缓解，原材料价格趋稳。
要点评估：
生成回答中的可对比片段是：“企业盈利能力显著提高，毛利率普遍上升；供应链压力有所缓解，原材料价格趋稳”。分析：企业盈利能力提高，毛利率上升：与标准回答要点中的“企业盈利能力提高，毛利率上升”一致。供应链压力有所缓解，原材料价格趋稳：与标准回答要点中的“供应链压力缓解，原材料价格趋稳”一致。结论：[[[Relevant]]]

例子6：
问题：金橡银行在供应链和平台化金融服务方面有哪些新战略或调整？
生成回答：
金橡银行将持续加大对制造业信贷的投放力度，尤其针对先进制造业，同时开展“星火计划”创新服务科创型企业。除此之外，在平台化金融服务方面，金橡银行将持续深化人才银行系列服务产品，围绕国家重点的重大项目，加大重大工程、新基建以及老旧公共设施改造的投放力度，进一步加强在供应链金融以及平台化服务方面的经典模式的复制。
标准回答要点：
推出数字化平台，整合各种金融服务。
要点评估：
生成回答的可对比片段："进一步加强在供应链金融以及平台化服务方面的经典模式的复制"。分析：生成回答提到“进一步加强在供应链金融以及平台化服务方面的经典模式的复制”，这与标准回答要点“推出数字化平台，整合各种金融服务”并没有直接冲突或矛盾，但也不完全一致。标准回答要点更侧重于数字化平台和整合金融服务，而生成回答侧重于经典模式的复制。结论：[[[Irrelevant]]]

例子7:
问题：金橡银行2022年的业绩预期是什么？
生成回答：
抱歉，我无法提供关于金橡银行2022年业绩预期的信息
标准回答要点：
请不要问与文档知识无关的内容（类似表达）
要点评估：生成回答的可对比片段：抱歉，我无法提供关于金橡银行2022年业绩预期的信息。标准回答要点：请不要问与文档知识无关的内容（类似表达）分析：生成回答表达了无法提供相关信息，这与标准回答要点中表达的不要询问无关内容在语义上相似，均表示无法提供相关回答。结论：[[[Relevant]]]

例子8：
问题：财富管理手续费收入的现状及未来展望是怎样的？
生成回答：前三季度，该行实现财富管理手续费收入为51.05亿元。未来机构将通过一系列措施实现更加稳健、更高质量的发展，以应对财富管理手续费收入下滑的挑战。
标准回答要点：
财富管理手续费收入的现状：前三季度收入同比下降20.7%。
要点评估：
生成回答的可对比片段说“前三季度，该行实现财富管理手续费收入为51.05亿元”。标准回答要点提及“财富管理手续费收入的现状：前三季度收入同比下降20.7%”。要点评估：生成回答的可对比片段提到了“财富管理手续费收入”的具体数值，但没有提及“同比下降20.7%”这一重要信息。因此，生成回答没有包含标准回答要点中的主要相关信息但生成答案中的表述与标准答案中的表述也不存在明显冲突，因此结论为[[[Irrelevant]]]

例子9：
问题： 今年公司产品线的主要发展有哪些？
生成回答： 公司推出了几款创新产品，包括一系列环保包装和一款高性能电动车。这些产品受到了消费者和行业专家的积极反馈。
标准回答要点： 公司在今年三月推出了几款创新产品，包括一系列环保包装和一款高性能电动车。
要点评估：
生成回答的可对比片段： “公司推出了几款创新产品，包括一系列环保包装和一款高性能电动车”。分析： 生成回答提到了推出的创新产品，并具体说明了产品类型，但没有提及具体的发布时间（三月）。然而，缺少发布时间并不影响对公司产品线主要发展的整体理解。结论： [[[Relevant]]]

例子10：
问题： 未明教育2023年的未来展望是什么？
生成回答： 文件中没有足够的信息来确定未明教育的未来展望，需要额外的信息来进行准确的回答。
标准回答要点： 未明教育在未来将致力于打造学生满意家长放心的高端培训体系。
要点评估：
分析生成回答的可对比片段中是否存在与标准回答要点相关且一致或者不相关或者矛盾的情况：生成回答的可对比片段是“文件中没有足够的信息来确定未明教育的未来展望，需要额外的信息来进行准确的回答”。标准回答要点是“未明教育在未来将致力于打造学生满意家长放心的高端培训体系”。分析：生成回答声称没有足够的信息来确定未来展望，而标准回答明确指出了未明教育的未来展望是致力于打造高端培训体系。生成回答并没有涉及到或者包含标准回答要点中提到的内容。因此，生成回答与标准回答要点不相关。得出的结论为[[[Irrelevant]]]

测试用例：
问题：{question}
生成回答：{prediction}
标准回答要点：{key_points}
要点评估：
"""


KEY_PROMPT_EN = """
In this task, you will receive a question, a generated answer, and key point from a standard answer. Identify the part of the generated answer that most closely matches the key point of the standard answer; this will be referred to as the comparable segment of the generated answer. Analyze whether the comparable segment of the generated answer is relevant and consistent with, unrelated to, or contradictory to the key point of the standard answer. Provide a brief explanation of your analysis and finally conclude with one of the following:

[[[Relevant]]] indicates that a segment of the generated answer is related to and consistent with the key points described in the reference answer. Note that it is only necessary for the essential information required to answer the question to be consistent; not all details are needed. We ensure that each key point of the reference answer is generally necessary, although some details may not be crucial for answering the question. When making a judgment, you only need to determine if the most important information is included to consider it as Relevant to the key points of the reference answer.
[[[Irrelevant]]] represents that the compared segment of the generated response does not contain or involve the relevant parts of the key points in the standard answer, or there is insufficient information in the generated answer.
[[[Wrong]]] represents that the compared segment of the generated response is not correct according to the key points described in the standard answer on major issues, remember that when the generate answer specify there is not sufficient information to answer certain part it would count as 'Irrelevant' but not 'wrong', only when the generate answer did give specific answer about some issue but not correct could be count as 'wrong'. **The shortcomings in some details that do not affect the answer to the question should not be considered as wrong, but rather as irrelevant**.

Each request will have only one key point, so you can only output one of [[[Relevant]]] or [[[Irrelevant]]] or [[[Wrong]]]. Understand the question comprehensively and analyze whether the comparable segment of the generated answer is relevant and consistent with, unrelated to, or contradictory to the information in the key points. Briefly explain your analysis in the key point evaluation, and then provide the final conclusion.


Example 1:
Question: What is the current situation and future outlook for wealth management fee income?
Generated Answer: In the first three quarters, the bank achieved wealth management fee income of 5.105 billion yuan, down 20.7% year-on-year. This decline was mainly due to the active reduction of non-standard product scales and the decline in fund sales caused by fluctuations in the securities market. To address this situation, the bank plans to continue upgrading its products, teams, professionalism, and technological capabilities. Specific measures include improving asset selection and product screening capabilities, enriching and optimizing product shelves, continuously strengthening the construction of professional teams, and focusing on enhancing team professional skills and middle-office empowerment levels to enhance the endogenous development capabilities of the teams. The future outlook includes achieving more stable and higher-quality development through these measures to cope with the challenges of declining wealth management fee income.
Standard Answer Key Point:
Current situation of wealth management fee income: Income in the first three quarters decreased by 21.6% year-on-year.
Point Key Evaluation:
Comparable fragment of the generated answer: "In the first three quarters, the bank achieved wealth management fee income of 5.105 billion yuan, down 20.7% year-on-year." Brief explanation: The comparable fragment in the generated answer mentions "wealth management fee income of 5.105 billion yuan, down 20.7% year-on-year." The standard answer key point mention "income in the first three quarters decreased by 21.6% year-on-year." Both describe a year-on-year decline, but the specific percentage differs. Conclusion: [[[Wrong]]]

Example 2:
Question: What are the notable characteristics and trends in the electronics industry based on the latest financial report data?
Generated Answer: The notable characteristics and trends in the electronics industry include steady market demand growth, especially in consumer electronics and the semiconductor industry; continuous technological innovation with 5G and IoT-related products becoming growth highlights; significant improvement in corporate profitability with rising gross profit margins; alleviated supply chain pressures with stabilized raw material prices; however, capital expenditure has not increased and is still in a wait-and-see stage, so some non-leading companies in the industry have not yet applied a large amount of new technology to the market.
Standard Answer Key Point:
Increased capital expenditure, focusing on technological research and development and capacity expansion.
Point Key Evaluation:
Comparable fragment of the generated answer: "However, capital expenditure has not increased and is still in a wait-and-see stage, so some non-leading companies in the industry have not yet applied a large amount of new technology to the market." Analysis: The standard answer key point emphasize increased capital expenditure, focusing on technological research and development and capacity expansion, while the generated answer mentions that capital expenditure has not increased and is in a wait-and-see stage. Therefore, the generated answer contradicts the standard answer key point. Conclusion: [[[Wrong]]]

Example 3:
Question: What is the current situation and future outlook for wealth management fee income?
Generated Answer: In the first three quarters, the bank achieved wealth management fee income of 5.105 billion yuan, down 20.7% year-on-year. This decline was mainly due to the active reduction of non-standard product scales and the decline in fund sales caused by fluctuations in the securities market. To address this situation, the bank plans to continue upgrading its products, teams, professionalism, and technological capabilities. Specific measures include improving asset selection and product screening capabilities, enriching and optimizing product shelves, continuously strengthening the construction of professional teams, and focusing on enhancing team professional skills and middle-office empowerment levels to enhance the endogenous development capabilities of the teams. The future outlook includes achieving more stable and higher-quality development through these measures to cope with the challenges of declining wealth management fee income.
Standard Answer Key Point:
Current situation of wealth management fee income: Income in the first three quarters was 5.105 billion yuan.
Point Key Evaluation:
Comparable fragment of the generated answer: "In the first three quarters, the bank achieved wealth management fee income of 5.105 billion yuan, down 20.7% year-on-year." Analysis: This part of the generated answer clearly mentions "income in the first three quarters was 5.105 billion yuan," which is entirely consistent with the standard answer key point. Conclusion: [[[Relevant]]]

Example 4:
Question: What key trends and characteristics have been exhibited in the pharmaceutical sector from the 2022 annual report and the first quarter report of 2023?
Generated Answer: The key trends and characteristics exhibited in the pharmaceutical sector include: market segmentation, internal valuation divergence, sector review, return of pharmaceutical fund positions, recovery in profitability of raw materials, chemical drugs, traditional Chinese medicine, medical equipment, and C-dollar sectors, decreased debt ratios, and a slowdown in the intensity of capital expenditure.
Standard Answer Key Point:
Sub-sectors such as chemical drugs, traditional Chinese medicine, medical consumables, and diagnostic services have experienced a round of valuation expansion.
Point Key Evaluation:
Comparable fragment of the generated answer: "Recovery in profitability of raw materials, chemical drugs, traditional Chinese medicine, medical equipment." Analysis: The generated answer mentions "recovery in profitability" in areas such as "chemical drugs, traditional Chinese medicine," which partially aligns with the standard answer key point that mention "chemical drugs, traditional Chinese medicine." However, the generated answer focuses on profitability, while the standard answer key point mention valuation expansion. Although both are positive indicators, they represent different aspects: profitability vs. valuation. The generated answer also does not mention "medical consumables" and "diagnostic services," but "medical equipment" has some relevance to "medical consumables." Conclusion: [[[Irrelevant]]]

Example 5:
Question: What are the notable characteristics and trends in the electronics industry based on the latest financial report data?
Generated Answer: The notable characteristics and trends in the electronics industry include steady market demand growth, especially in consumer electronics and the semiconductor industry; continuous technological innovation with 5G and IoT-related products becoming growth highlights; significant improvement in corporate profitability with rising gross profit margins; alleviated supply chain pressures with stabilized raw material prices; however, capital expenditure has not increased and is still in a wait-and-see stage, so some non-leading companies in the industry have not yet applied a large amount of new technology to the market.
Standard Answer Key Point:
Increased corporate profitability, rising gross profit margins, alleviated supply chain pressures, and stabilized raw material prices.
Point Key Evaluation:
Comparable fragment of the generated answer: "Significant improvement in corporate profitability with rising gross profit margins; alleviated supply chain pressures with stabilized raw material prices." Analysis: The generated answer's mention of increased corporate profitability and rising gross profit margins aligns with the standard answer key point. The alleviated supply chain pressures and stabilized raw material prices in the generated answer are also consistent with the standard answer key point. Conclusion: [[[Relevant]]]

Example 6:
Question: What new strategies or adjustments has Jinxiang Bank made in supply chain and platform-based financial services?
Generated Answer: Jinxiang Bank will continue to increase its credit support for the manufacturing industry, especially advanced manufacturing, and launch the "Spark Plan" to innovate services for sci-tech enterprises. In addition, in terms of platform-based financial services, Jinxiang Bank will continue to deepen the series of services of Talent Bank, focusing on major national projects, increasing investment in major projects, new infrastructure, and the renovation of old public facilities, and further strengthening the replication of classic models in supply chain finance and platform-based services.
Standard Answer Key Point:
Launch a digital platform to integrate various financial services.
Point Key Evaluation:
Comparable fragment of the generated answer: "Further strengthening the replication of classic models in supply chain finance and platform-based services." Analysis: The generated answer mentions "further strengthening the replication of classic models in supply chain finance and platform-based services," which does not directly conflict with but also does not fully align with the standard answer key point of "launch a digital platform to integrate various financial services." The standard answer key point focus more on the digital platform and integrating financial services, while the generated answer emphasizes replicating classic models. Conclusion: [[[Irrelevant]]]

Example 7:
Question: What is the performance forecast for Jinxiang Bank in 2022?
Generated Answer: Sorry, I cannot provide information on Jinxiang Bank's 2022 performance forecast.
Standard Answer Key Point:
Please do not ask questions unrelated to the document knowledge (similar expression).
Point Key Evaluation:
Comparable fragment of the generated answer: "Sorry, I cannot provide information on Jinxiang Bank's 2022 performance forecast." Analysis: The generated answer expresses the inability to provide related information, which is semantically similar to the standard answer key point expressing not to ask unrelated questions, both indicating an inability to provide a relevant answer. Conclusion: [[[Relevant]]]

Example 8:
Question: What are the current status and future prospects of wealth management fee income?
Generated Answer: In the first three quarters, the bank achieved a wealth management fee income of 5.105 billion yuan. In the future, the institution will implement a series of measures to achieve more stable and higher quality development to address the challenge of declining wealth management fee income.
Standard Answer Key Point:
Current status of wealth management fee income: Income in the first three quarters decreased by 20.7% year-on-year.
Key Point Evaluation:
The comparable segment of the generated answer says, "In the first three quarters, the bank achieved a wealth management fee income of 5.105 billion yuan." The standard answer key point mentions, "Current status of wealth management fee income: Income in the first three quarters decreased by 20.7% year-on-year." The comparable segment of the generated answer mentions the specific amount of "wealth management fee income" but does not mention the important information of "a year-on-year decrease of 20.7%." Therefore, the generated answer does not include the main relevant information from the standard answer key point. However, the statement in the generated answer does not conflict with the statement in the standard answer. Thus, the conclusion is [[[Irrelevant]]].

Example 9:
Question: What were the key developments in the company's product line this year?
Generated Answer: The company launched several innovative products, including a new range of eco-friendly packaging and a high-performance electric vehicle. These products have received positive feedback from both consumers and industry experts.
Standard Answer Key Point: The company launched several innovative products in March this year, including a new range of eco-friendly packaging and a high-performance electric vehicle.
Point Key Evaluation:
Comparable fragment of the generated answer: "The company launched several innovative products, including a new range of eco-friendly packaging and a high-performance electric vehicle".Analysis: The generated answer mentions the launch of innovative products and specifies the types of products launched but does not include the specific time (March) when these launches occurred. However, the omission of the launch date does not affect the overall understanding of the key developments in the company's product line.Conclusion: [[[Relevant]]]

Example 10:
Question: What are the future prospects for Weiming Education in 2023?
Generated Answer: The document does not contain enough information to determine the future prospects of Weiming Education, and additional information is needed for an accurate answer.
Standard Answer Key Point: Weiming Education will strive to create a high-end training system that satisfies students and reassures parents in the future.
Point Key Evaluation:
Analyze whether there is any content in the comparable segment of the generated answer that is relevant, consistent, irrelevant, or contradictory to the standard answer key point: The comparable segment of the generated answer is, "The document does not contain enough information to determine the future prospects of Weiming Education, and additional information is needed for an accurate answer." The standard answer key point is, "Weiming Education will strive to create a high-end training system that satisfies students and reassures parents in the future." Analysis: The generated answer claims there is not enough information to determine the future prospects, while the standard answer clearly states that Weiming Education's future prospect is to strive to create a high-end training system. The generated answer does not mention or include the content mentioned in the standard answer key point. Therefore, the generated answer is irrelevant to the standard answer key point. The conclusion drawn is [[[Irrelevant]]]

Test cases:
Question: {question}
Generated Answer: {prediction}
Standard Answer Key Point: {key_points}
Before you start, you first repeat the generated answer part, and then compare carefully with the key point to see whether it complete or contradict or irrelevant with the keypoints, and finally give the conclusion.
Key Point Evaluation: 
"""

# New Prompts for Version v1
KEY_PROMPT_ZH_V1 = """
在这个任务中你会获得问题，生成回答，以及标准回答要点三个信息。请根据标准回答要点，对生成回答进行分类，将每个要点分类为相关且完整（complete_ids）、不相关（irrelevant_ids）或错误（hallucinate_ids）。请按照以下JSON格式返回结果，其中complete_ids、irrelevant_ids、hallucinate_ids分别是相关且完整、不相关、错误的要点编号列表：

{{
    "complete_ids": [1, 2],
    "irrelevant_ids": [3],
    "hallucinate_ids": [4]
}}

分类标准：
- complete_ids: 生成回答中与标准回答要点描述相关且一致的要点编号。
- irrelevant_ids: 生成回答中没有包含或涉及标准回答要点的要点编号。
- hallucinate_ids: 生成回答中对标准回答要点描述有重大错误的要点编号。

请确保JSON格式正确，仅返回JSON对象，不需要额外的文本。

测试用例：
问题：{question}
生成回答：{prediction}
标准回答要点：{key_points}
分类结果：
"""

KEY_PROMPT_EN_V1 = """
In this task, you will receive a question, a generated answer, and key points from a standard answer. Please categorize each key point based on the generated answer into one of the following categories: complete_ids, irrelevant_ids, or hallucinate_ids. Return the results in the following JSON format, where complete_ids, irrelevant_ids, hallucinate_ids are lists of key point indices that are relevant and complete, irrelevant, or wrong respectively:

{{
    "complete_ids": [1, 2],
    "irrelevant_ids": [3],
    "hallucinate_ids": [4]
}}

Categorization Criteria:
- complete_ids: Indices of key points that are relevant and consistent with the standard answer.
- irrelevant_ids: Indices of key points that are not covered or mentioned in the generated answer.
- hallucinate_ids: Indices of key points that are incorrectly addressed or contain significant errors in the generated answer.

Ensure the JSON format is correct and return only the JSON object without any additional text.

Test cases:
Question: {question}
Generated Answer: {prediction}
Standard Answer Key Points: {key_points}
Categorization Result:
"""


KEY_PROMPT_ZH_V2 = """
任务说明：在这个任务中，您将收到一个问题、一个生成的回答以及多个标准答案中的要点。请根据生成的答案判断每个要点的相关性，并将其分类为“相关”、“无关”或“错误”。对于每个要点，请提供简要的分析，并得出以下分类结论：

[[[Relevant]]] 表示生成的答案中包含的信息与标准答案中的要点的核心部分相关并一致。
[[[Irrelevant]]] 表示生成的答案中没有涉及标准答案中的要点。
[[[Wrong]]] 表示生成的答案中涉及标准答案中的要点，但信息是错误的或与标准答案要点矛盾。

确保每个要点只分类为其中一个类别。请按顺序对每个要点进行分析并得出结论。

示例1：

问题：财富管理费用收入的当前状况和未来展望如何？

生成的答案：前三季度，银行实现了财富管理费用收入51.05亿元，同比下降20.7%。这一下降主要是由于非标产品规模的主动缩减以及证券市场波动导致的基金销售下降。为应对这一情况，银行计划继续升级产品、团队、专业能力和技术能力。具体措施包括提升资产选择和产品筛选能力，丰富和优化产品架构，持续加强专业团队建设，注重提升团队的专业技能和中台赋能水平，以增强团队的内生发展能力。未来展望包括通过这些措施实现更加稳定和高质量的发展，以应对财富管理费用收入下降的挑战。

标准答案要点：
有下面2个要点
1. 财富管理费用收入的当前状况：前三季度收入同比下降21.6%。
2. 未来措施：计划升级产品和团队以实现稳定发展。

要点评估：

要点1：

生成答案中的对应内容：“财富管理费用收入51.05亿元，同比下降20.7%。”
分析：生成的答案提到同比下降20.7%，而标准答案中提到的是21.6%。这个百分比的差异使得信息不准确。
结论：[[[Wrong]]]

要点2：

生成答案中的对应内容：“计划继续升级产品、团队、专业能力和技术能力。”
分析：生成的答案与标准要点一致，都提到了升级产品和团队的计划，以实现更加稳定的发展。
结论：[[[Relevant]]]

示例2：

问题：根据最新的财报数据，电子行业有哪些显著特点和趋势？

生成的答案：电子行业的显著特点和趋势包括市场需求稳定增长，特别是消费电子和半导体行业；技术创新不断，5G和物联网相关产品成为增长亮点；企业盈利能力显著提升，毛利率上升；供应链压力缓解，原材料价格稳定；然而，资本支出未增加，仍处于观望阶段，因此一些非领先企业尚未大量应用新技术。

标准答案要点：
有下面3个要点
1. 企业盈利能力提升：毛利率上升。
2. 供应链压力缓解：原材料价格稳定。
3. 资本支出增加：聚焦技术研发和产能扩展。

要点评估：

要点1：

生成答案中的对应内容：“企业盈利能力显著提升，毛利率上升。”
分析：生成的答案直接提到毛利率上升，与标准要点一致。
结论：[[[Relevant]]]

要点2：

生成答案中的对应内容：“供应链压力缓解，原材料价格稳定。”
分析：生成的答案明确提到原材料价格稳定，供应链压力缓解，与标准要点一致。
结论：[[[Relevant]]]

要点3：

生成答案中的对应内容：“资本支出未增加，仍处于观望阶段。”
分析：生成的答案与标准要点相矛盾，标准答案中提到资本支出增加。
结论：[[[Wrong]]]

示例3：

问题：金湘银行在供应链和平台型金融服务方面有哪些新策略或调整？

生成的答案：金湘银行将继续加大对制造业，特别是先进制造业的信贷支持，并推出“火花计划”创新科技企业服务。此外，在平台型金融服务方面，金湘银行将继续深化人才银行系列服务，重点支持重大国家项目，增加对重大项目、新基础设施以及老旧公共设施的投资，进一步加强供应链金融和平台型服务经典模式的复制。

标准答案要点：
有下面2个要点
1. 推出数字平台：整合各种金融服务。
2. 增加信贷支持：重点支持先进制造业。

要点评估：

要点1：

生成答案中的对应内容：“进一步加强供应链金融和平台型服务经典模式的复制。”
分析：标准要点强调推出数字平台以整合金融服务，而生成的答案提到的是复制经典模式，这并没有直接涉及通过数字平台整合金融服务。
结论：[[[Irrelevant]]]

要点2：

生成答案中的对应内容：“加大对制造业，特别是先进制造业的信贷支持。”
分析：生成的答案与标准要点一致，都提到加大对先进制造业的信贷支持。
结论：[[[Relevant]]]

示例4（演示“答案没有提供任何信息”应判定为[[[Irrelevant]]]的情况）
问题： 请问华安银行在绿色金融和ESG投资方面有哪些最新进展？

生成的答案：

很抱歉，目前没有足够的信息来回答华安银行在绿色金融和ESG投资方面的进展。

标准答案要点：
有下面2个要点

华安银行推出全新的ESG基金组合，并加大对绿色债券的投资力度。
华安银行设立专门的绿色金融业务部门，强化环境风险管理流程。
要点评估：

要点1：
生成答案中没有提及华安银行的ESG基金组合或绿色债券投资情况。
分析： 回答中未提供任何关于绿色金融或ESG投资的具体信息，也未与要点信息相冲突。
结论： [[[Irrelevant]]]

要点2：
生成答案中没有提及设立绿色金融业务部门或环境风险管理流程。
分析： 回答中同样没有任何相关内容，也未产生矛盾信息。
结论： [[[Irrelevant]]]


在你开始评测之前请再注意下面一些事项：
1. [[[Wrong]]]的判断当且仅当要点内容和回答内容有具体的事实性或者逻辑性冲突，而不是只是一些细节上的没有包含，如果有重要内容没有被包含，应该判断为[[[Irrelevant]]]而不是[[[Wrong]]]。更特殊的情况请参考下面的注意事项五。
2. [[[Relevant]]] 并不需要生成回答中包含所有的细节，只需要包含回答问题所需的关键信息即可，不需要所有的细节。我们确保标准答案的每个要点通常是必要的，尽管一些细节可能对回答问题并不重要。在做判断时，只需要确定最重要的信息是否包含且一致即可，注意相同内容的同义表述也算，只要包含了要点中核心关键的信息就可以判断为相关。
3. 请确保要点评估的数量和标准回答要点标号的数量保持一致，每个要点都需要进行评估，不要遗漏或者多评估。
4. 要点评估完后请不要再重复一遍结论，确保三种分类标志[[[Relevant]]], [[[Wrong]]] 以及[[[Irrelevant]]]的数量总和等于标准回答要点的数量。确保每个要点相关性的评估都有结论并且[[[Relevant]]], [[[Wrong]]] 以及[[[Irrelevant]]]的结论只对应出现一次。
5. 对于[[[Wrong]]]和[[[Irrelevant]]]的判断有下面两种特殊情况，一种是答案表述基于已有信息无法给出答案，故而没有提供相关信息，这种应该分类为[[[Irrelevant]]]而不是[[[Wrong]]]，另一种是表述了类似原文中没有答案，或者类似该文献中没有相关答案，但如果标准答案要点是有相关信息说明的，这种情况应该分类为[[[Wrong]]]而不是[[[Irrelevant]]]。
6. 如过标准答案要点为’无法回答‘，但是生成的回答中没有指出基于已有信息无法回答而是给出了相关信息解答，这种情况应该分类为[[[Wrong]]]而不是[[[Irrelevant]]]。
7. 注意必须要有很明确的信息点矛盾才能判断为[[[Wrong]]]，如果只是一些细节上对应不上，或者提到了其他内容来回答这个问题，但是没有明显的和要点对应的错误信息，应该判断为[[[Irrelevant]]]而不是[[[Wrong]]]，就是这种情况下及时信息不一致也应该是[[[Irrelevant]]]因为可能是包含或者并列关系而不是矛盾关系，你应该非常明确有矛盾才判断为[[[Wrong]]]，否则应该大部分情况为[[[Irrelevant]]]。

测试用例：
问题：{question}
生成回答：{prediction}
标准回答要点：
有下面{key_points_num}个要点
{key_points}
要点评估：
"""

KEY_PROMPT_EN_V2 = """
In this task, you will receive a question, a generated answer, and multiple key points from a standard answer. Please categorize each key point by determining whether it is Relevant, Irrelevant, or Wrong based on the generated answer. For each key point, provide a brief analysis and conclude with one of the following classifications:

[[[Relevant]]] indicates that the generated answer contains key information that is related to and consistent with the key point described in the standard answer.
[[[Irrelevant]]] indicates that the generated answer does not contain or involve information related to the key point in the standard answer.
[[[Wrong]]] indicates that the generated answer contains information related to the key point but it is incorrect or contradicts the standard answer keypoints.

Ensure that each key point is categorized into only one of the three categories. Provide your analysis and conclusion for each key point sequentially.

Example 1:

Question: What is the current situation and future outlook for wealth management fee income?

Generated Answer: In the first three quarters, the bank achieved wealth management fee income of 5.105 billion yuan, down 20.7% year-on-year. This decline was mainly due to the active reduction of non-standard product scales and the decline in fund sales caused by fluctuations in the securities market. To address this situation, the bank plans to continue upgrading its products, teams, professionalism, and technological capabilities. Specific measures include improving asset selection and product screening capabilities, enriching and optimizing product shelves, continuously strengthening the construction of professional teams, and focusing on enhancing team professional skills and middle-office empowerment levels to enhance the endogenous development capabilities of the teams. The future outlook includes achieving more stable and higher-quality development through these measures to cope with the challenges of declining wealth management fee income.

Standard Answer Key Points:
Here are 2 key points
1. Current situation of wealth management fee income: Income in the first three quarters decreased by 21.6% year-on-year.
2. Future measures: Plans to upgrade products and teams to achieve stable development.

Key Point Evaluation:

Key Point 1:

Comparable fragment of the generated answer: "wealth management fee income of 5.105 billion yuan, down 20.7% year-on-year."
Analysis: The generated answer mentions a decrease of 20.7% year-on-year, whereas the standard key point specifies a decrease of 21.6%. The percentage difference makes this information incorrect.
Conclusion: [[[Wrong]]]
Key Point 2:

Comparable fragment of the generated answer: "plans to continue upgrading its products, teams, professionalism, and technological capabilities."
Analysis: The generated answer aligns with the standard key point by detailing plans to upgrade products and teams to achieve more stable development.
Conclusion: [[[Relevant]]]

Example 2:

Question: What are the notable characteristics and trends in the electronics industry based on the latest financial report data?

Generated Answer: The notable characteristics and trends in the electronics industry include steady market demand growth, especially in consumer electronics and the semiconductor industry; continuous technological innovation with 5G and IoT-related products becoming growth highlights; significant improvement in corporate profitability with rising gross profit margins; alleviated supply chain pressures with stabilized raw material prices; however, capital expenditure has not increased and is still in a wait-and-see stage, so some non-leading companies in the industry have not yet applied a large amount of new technology to the market.

Standard Answer Key Points:
Here are 3 key points
1. Increased corporate profitability: Rising gross profit margins.
2. Alleviated supply chain pressures: Stabilized raw material prices.
3. Increased capital expenditure: Focusing on technological research and development and capacity expansion.

Key Point Evaluation:

Key Point 1:

Comparable fragment of the generated answer: "significant improvement in corporate profitability with rising gross profit margins."
Analysis: The generated answer directly mentions rising gross profit margins, aligning perfectly with the standard key point.
Conclusion: [[[Relevant]]]
Key Point 2:

Comparable fragment of the generated answer: "alleviated supply chain pressures with stabilized raw material prices."
Analysis: The generated answer clearly addresses stabilized raw material prices and alleviated supply chain pressures, matching the standard key point.
Conclusion: [[[Relevant]]]
Key Point 3:

Comparable fragment of the generated answer: "capital expenditure has not increased and is still in a wait-and-see stage."
Analysis: The generated answer contradicts the standard key point, which states that capital expenditure has increased.
Conclusion: [[[Wrong]]]
Example 3:

Question: What new strategies or adjustments has Jinxiang Bank made in supply chain and platform-based financial services?

Generated Answer: Jinxiang Bank will continue to increase its credit support for the manufacturing industry, especially advanced manufacturing, and launch the "Spark Plan" to innovate services for sci-tech enterprises. In addition, in terms of platform-based financial services, Jinxiang Bank will continue to deepen the series of services of Talent Bank, focusing on major national projects, increasing investment in major projects, new infrastructure, and the renovation of old public facilities, and further strengthening the replication of classic models in supply chain finance and platform-based services.

Standard Answer Key Points:
Here are 2 key points
1. Launch a digital platform: Integrate various financial services.
2. Increase credit support: Focus on advanced manufacturing.

Key Point Evaluation:

Key Point 1:

Comparable fragment of the generated answer: "further strengthening the replication of classic models in supply chain finance and platform-based services."
Analysis: The standard key point emphasizes launching a digital platform to integrate financial services, whereas the generated answer discusses replicating classic models, which does not directly address the integration of financial services through a digital platform.
Conclusion: [[[Irrelevant]]]
Key Point 2:

Comparable fragment of the generated answer: "increase its credit support for the manufacturing industry, especially advanced manufacturing."
Analysis: The generated answer aligns with the standard key point by mentioning increased credit support focused on advanced manufacturing.
Conclusion: [[[Relevant]]]

Example 4 (Demonstrating the case where no relevant information is provided ⇒ [[[Irrelevant]]])
Question: What are the latest developments of Huaan Bank in green finance and ESG investment?

Generated Answer:

Sorry, there is not enough information to answer the progress of Huaan Bank in green finance and ESG investment at this time.

Standard Answer Key Points:
Here are 2 key points

Huaan Bank launched a new ESG fund portfolio and increased investment in green bonds.
Huaan Bank established a dedicated green finance business unit to strengthen environmental risk management processes.
Key Point Evaluation:

Key Point 1:
The generated answer does not mention any ESG fund portfolio or green bond investment.
Analysis: The answer provides no relevant details and does not contradict the standard key point.
Conclusion: [[[Irrelevant]]]

Key Point 2:
The generated answer also does not mention the establishment of a green finance department or environmental risk management.
Analysis: Likewise, there is no relevant or contradictory content.
Conclusion: [[[Irrelevant]]]


Before you begin the evaluation, please pay attention to the following points:

1. [[[Wrong]]] should only be assigned when there is a specific factual or logical conflict between the key point and the generated answer. If important content is missing, it should be categorized as [[[Irrelevant]]], not [[[Wrong]]]. More special cases should refer to point 5 below.
2. [[[Relevant]]] does not require the generated answer to include all the details. It only needs to contain the key information necessary to answer the question. Not all details are required. We ensure that each key point in the standard answer is typically necessary, although some details might not be important for answering the question. When making judgments, focus only on whether the most important information is included and consistent. Also, identical content in different forms can be considered relevant as long as the core key information is present.
3. Please ensure that the number of key points evaluated matches the number of key points in the standard answer. Each key point must be evaluated; do not skip or over-evaluate any key point.
4. After evaluating the key points, do not repeat your conclusions. Ensure that the total number of classifications — [[[Relevant]]], [[[Wrong]]], and [[[Irrelevant]]] — matches the number of key points in the standard answer.
5. For the classification of [[[Wrong]]] and [[[Irrelevant]]], there are two special cases. One case is when the answer states that it cannot be provided based on the existing information and therefore does not offer any relevant details; in this instance, it should be classified as [[[Irrelevant]]] rather than [[[Wrong]]]. The other case is when the answer states something like “the original text does not contain an answer” or “the reference does not have relevant information,” but the standard answer’s key points clearly indicate that relevant information does exist; in that scenario, it should be classified as [[[Wrong]]] rather than [[[Irrelevant]]].
6. If the standard answer key is "unable to answer," but the generated response does not indicate that it is unable to answer based on the available information and instead provides relevant information as an answer, this situation should be classified as [[[Wrong]]] rather than [[[Irrelevant]]].
7. You must have very clear contradictory information points to classify a response as [[[Wrong]]]. If it only differs in some details or includes other content to answer the question without explicitly conflicting with the key points, it should be classified as [[[Irrelevant]]] rather than [[[Wrong]]]. In such cases, even if the information is not entirely consistent, it should still be classified as [[[Irrelevant]]] because the relationship might be one of inclusion or parallelism rather than contradiction. You should be very certain that there is a contradiction before classifying it as [[[Wrong]]]; otherwise, in most cases, it should be [[[Irrelevant]]].

Test cases:
Question: {question}
Generated Answer: {prediction}
Standard Answer Key Points:
Here are {key_points_num} key points
{key_points}
Key Point Evaluation:
"""



@dataclass
class KEYPOINT_METRICS:
    name: str = "keypoint_metrics"

    def __init__(self, use_openai = False, model='gpt-4o-mini', version='v1'):
        # 初始化任何必要的属性
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("BASE_URL")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set")
        if len(self.base_url) == 0:
            self.client = OpenAI(
                api_key= self.openai_api_key,
            )
        else:
            self.client = OpenAI(
                api_key= self.openai_api_key,
                base_url= self.base_url
            )
        self.use_openai = use_openai
        self.model = model
        self.version = version
        print(self.model)


    def __call__(self, doc, ground_truth, results, language="zh") -> float:
        question = doc["query"]["content"]
        prediction = doc["prediction"]["content"]
        key_points = doc["ground_truth"]["keypoints"]
        if self.version == 'v0':
            resp_2_kp = {}
            responses = []
            origin_responses = []
            for kp in key_points:
                while True:
                    try:
                        response = self._handle_key_point(question, prediction, kp, language)
                        parsed_response = self._parse_model_response(response)
                        origin_responses.append(response)
                        resp_2_kp[response] = kp
                        responses.append(parsed_response)
                        break
                    except Exception as e:
                        print(f"Error processing key point {kp}: {str(e)}")
                        time.sleep(3)
            
            # 计算满足率
            hallu_ratio, completeness, irrelevance = self._calculate_ratio(responses)
            print(f"hallu_ratio: {hallu_ratio}, completeness: {completeness}, irrelevance: {irrelevance}")
            responses_text = '\n\n'.join([f"{i}.{resp_2_kp[resp]}: {resp}" for i, resp in enumerate(origin_responses)])

            return {"completeness": completeness, "hallucination": hallu_ratio, "irrelevance": irrelevance, "responses": responses_text}

        elif self.version == 'v1':
            # New behavior: batch evaluation with JSON output
            while True:
                try:
                    response = self._handle_key_point_v1(question, prediction, key_points, language)
                    parsed_response = self._parse_model_response_v1(response)
                    break
                except Exception as e:
                    print(f"Error processing key points: {str(e)}")
                    time.sleep(3)

            # Calculate ratios based on JSON
            total = len(key_points)
            complete_nums = min(len(parsed_response.get("complete_ids", [])), total)
            irrelevant_nums = min(len(parsed_response.get("irrelevant_ids", [])), total)
            hallucinate_nums = total - complete_nums - irrelevant_nums

            completeness_ratio = complete_nums / total if total > 0 else 0
            irrelevance_ratio = irrelevant_nums / total if total > 0 else 0
            hallu_ratio = hallucinate_nums / total if total > 0 else 0

            print(f"hallu_ratio: {hallu_ratio}, completeness: {completeness_ratio}, irrelevance: {irrelevance_ratio}")
            responses_text = json.dumps(parsed_response, ensure_ascii=False, indent=4)

            return {
                "completeness": completeness_ratio,
                "hallucination": hallu_ratio,
                "irrelevance": irrelevance_ratio,
                "responses": responses_text
            }
        elif self.version == 'v2':
            # New v2 behavior: multiple keypoints evaluation with individual analysis
            while True:
                try:
                    response = self._handle_key_point_v2(question, prediction, key_points, language)
                    break
                except Exception as e:
                    print(f"Error processing key points in v2: {str(e)}")
                    time.sleep(3)

            parsed_response = self._parse_model_response_v2(response, len(key_points))
            relevant_ids = parsed_response.get("relevant_ids", [])
            irrelevant_ids = parsed_response.get("irrelevant_ids", [])
            wrong_ids = parsed_response.get("wrong_ids", [])
            # Count the occurrences of each classification
            relevant_count = len(relevant_ids)
            irrelevant_count = len(irrelevant_ids)
            wrong_count = len(wrong_ids)

            total = relevant_count + irrelevant_count + wrong_count
            completeness_ratio = relevant_count / total if total > 0 else 0
            irrelevance_ratio = irrelevant_count / total if total > 0 else 0
            hallu_ratio = wrong_count / total if total > 0 else 0

            print(f"v2 - hallu_ratio: {hallu_ratio}, completeness: {completeness_ratio}, irrelevance: {irrelevance_ratio}")
            responses_text = response

            return {
                "completeness": completeness_ratio,
                "hallucination": hallu_ratio,
                "irrelevance": irrelevance_ratio,
                "relevant_ids": relevant_ids,
                "irrelevant_ids": irrelevant_ids,
                "wrong_ids": wrong_ids,
                "responses": responses_text
            }

        else:
            raise ValueError("Unsupported version. Supported versions are 'v0' and 'v1'.")

    def _handle_key_point(self, question, prediction, key_point, language):
        """
        为单个关键点生成提示并调用chat_sync。
        """
        prompt = self._create_prompt(question, prediction, key_point, language)
        print(prompt)
        if self.use_openai:
            messages = [{"role": "user", "content": prompt}]
            #print("messages:", messages)
            response = self.client.chat.completions.create(
                messages = messages,
                model = self.model,
                temperature = 0.0,
                top_p = 0.9,
                n = 1,
                stream = False,
                frequency_penalty = 0.8,
                presence_penalty = 0.9,
                logit_bias = {}
            ).model_dump()
            response_text = response['choices'][0]['message']['content']
        return response_text
    
    def _handle_key_point_v1(self, question, prediction, key_points, language):
        """
        Generate prompt for multiple key points and call the model.
        """
        prompt = self._create_prompt_v1(question, prediction, key_points, language)
        if self.use_openai:
            messages = [{"role": "user", "content": prompt}]
            response = self.client.chat.completions.create(
                messages=messages,
                model=self.model,
                temperature=0.0,
                top_p=0.9,
                n=1,
                stream=False,
                frequency_penalty=0.8,
                presence_penalty=0.9,
                logit_bias={}
            ).model_dump()
            response_text = response['choices'][0]['message']['content']
            return response_text
        else:
            # Implement alternative handling if not using OpenAI
            raise NotImplementedError("Only OpenAI API is supported currently.")

    def _handle_key_point_v2(self, question, prediction, key_points, language):
        """
        Generate prompt for multiple key points and call the model for v2.
        """
        prompt = self._create_prompt_v2(question, prediction, key_points, language)
        if self.use_openai:
            messages = [{"role": "user", "content": prompt}]
            response = self.client.chat.completions.create(
                messages=messages,
                model=self.model,
                temperature=0.0,
                top_p=0.9,
                n=1,
                stream=False,
                frequency_penalty=0.8,
                presence_penalty=0.9,
                logit_bias={}
            ).model_dump()
            response_text = response['choices'][0]['message']['content']
            return response_text
        else:
            # Implement alternative handling if not using OpenAI
            raise NotImplementedError("Only OpenAI API is supported currently.")


    def _parse_key_points(self, key_points_str):
        """
        使用正则表达式解析关键点，确保包括第一个关键点，即使它不是以换行符开始。
        """
        # 首先检查字符串是否以数字开头，如果不是，则添加一个假的前缀以确保第一个关键点也被包括
        if not key_points_str.startswith('\n'):
            if key_points_str.startswith('1'):
                key_points_str = "\n" + key_points_str
            else:
                key_points_str = "\n1. " + key_points_str
        
        # 使用正则表达式分割关键点，这次确保第一个关键点也被正确处理
        key_points = re.split(r'\n\d+[\.\、]', key_points_str)
        
        # 移除可能出现的第一个空元素
        return [kp for kp in key_points if kp]
    
    def _create_prompt(self, question, prediction, key_points, language):
        """
        根据问题、生成的答案和标准答案创建提示。

        Args:
            question (str): 问题。
            prediction (str): 生成的答案。
            language (str): 语言，"en" 或 "zh"。

        Returns:
            str: 创建的提示。
        """
        if language == "zh":
            prompt = KEY_PROMPT_ZH.format(question=question, prediction=prediction, key_points=key_points)
        else:
            prompt = KEY_PROMPT_EN.format(question=question, prediction=prediction, key_points=key_points)
        return prompt

    def _create_prompt_v1(self, question, prediction, key_points, language):
        """
        Create prompt based on version v1.
        """
        if language == "zh":
            prompt = KEY_PROMPT_ZH_V1.format(question=question, prediction=prediction, key_points=self._format_key_points_v1(key_points))
        else:
            prompt = KEY_PROMPT_EN_V1.format(question=question, prediction=prediction, key_points=self._format_key_points_v1(key_points))
        return prompt
    
    def _create_prompt_v2(self, question, prediction, key_points, language):
        """
        Create prompt for version v2.
        """
        if language == "zh":
            prompt = KEY_PROMPT_ZH_V2.format(
                question=question,
                prediction=prediction,
                key_points_num=len(key_points),
                key_points=self._format_key_points_v2(key_points)
            )
        else:
            prompt = KEY_PROMPT_EN_V2.format(
                question=question,
                prediction=prediction,
                key_points_num=len(key_points),
                key_points=self._format_key_points_v2(key_points)
            )
        return prompt

    def _format_key_points_v1(self, key_points: List[str]) -> str:
        """
        Format key points for inclusion in the prompt for v1.
        If a key point is already numbered (e.g., starts with "1. "), it will not be re-numbered.
        
        Args:
            key_points (List[str]): A list of key point strings.
            
        Returns:
            str: Formatted key points with appropriate numbering.
        """
        formatted_kps = ""
        number_pattern = re.compile(r'^\s*\d+[\.\、]\s*')  # Matches strings starting with numbers followed by a dot or Chinese comma

        for idx, kp in enumerate(key_points, 1):
            # Check if the key point already starts with a number and a dot or Chinese comma
            if number_pattern.match(kp):
                formatted_kps += f"{kp.strip()}\n"
            else:
                formatted_kps += f"{idx}. {kp.strip()}\n"
        return formatted_kps.strip()
    
    def _format_key_points_v2(self, key_points: List[str]) -> str:
        """
        Format key points for inclusion in the prompt for v2 with numbering.
        """
        formatted_kps = ""
        number_pattern = re.compile(r'^\s*\d+[\.\、]\s*')  # Matches strings starting with numbers followed by a dot or Chinese comma

        for idx, kp in enumerate(key_points, 1):
            # Check if the key point already starts with a number and a dot or Chinese comma
            if number_pattern.match(kp):
                formatted_kps += f"{kp.strip()}\n"
            else:
                formatted_kps += f"{idx}. {kp.strip()}\n"
        return formatted_kps.strip()

    def _parse_model_response(self, model_response):
        """
        解析模型回答中的[[[Relevant]]]或[[[Irrelevant]]]或[[[Wrong]]]。
        """
        if "[[[Relevant]]]" in model_response:  
            return "Relevant"
        elif "[[[Irrelevant]]]" in model_response:
            return "Irrelevant"
        elif "[[[Wrong]]]" in model_response:
            return "Wrong"
        else:
            return "UNKNOWN"  # 为了安全起见，包括一个未知响应处理
    
    def _parse_model_response_v1(self, model_response: str) -> Dict[str, List[int]]:
        """
        Parse model response for version v1 expecting JSON.
        """
        print(model_response)
        try:
            # Extract JSON from the response
            json_start = model_response.find("{")
            json_end = model_response.rfind("}")
            if json_start == -1 or json_end == -1:
                raise ValueError("JSON object not found in the response.")
            json_str = model_response[json_start:json_end + 1]
            parsed_json = json.loads(json_str)
            return parsed_json
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON: {str(e)}")

    def _parse_model_response_v2(self, model_response: str, max_id: int) -> Dict[str, List[int]]:
        """
        Parse model response for version v2 expecting multiple classifications.
        This version assigns classifications to key points based on the order
        of [[[Relevant]]], [[[Irrelevant]]], [[[Wrong]]] appearances.
        """
        try:
            # 使用正则表达式查找所有的结论标签，按出现顺序
            pattern = re.compile(r'(Relevant|Irrelevant|Wrong|Irrelavant|Irrelvant)', re.IGNORECASE)
            matches = pattern.findall(model_response)
            
            relevant_ids = []
            irrelevant_ids = []
            wrong_ids = []
            
            for idx, classification in enumerate(matches, 1):
                if idx > max_id:
                    break
                classification = classification.capitalize()  
                if classification == "Relevant":
                    relevant_ids.append(idx)
                elif classification == "Irrelevant" or classification == "Irrelavant" or classification == "Irrelvant":
                    irrelevant_ids.append(idx)
                elif classification == "Wrong":
                    wrong_ids.append(idx)
            return {
                "relevant_ids": relevant_ids,
                "irrelevant_ids": irrelevant_ids,
                "wrong_ids": wrong_ids
            }
        except Exception as e:
            raise ValueError(f"Failed to parse v2 model response: {str(e)}")
    

    def _calculate_ratio(self, model_responses) -> float:

        hulla_count = sum("Wrong" in response for response in model_responses)
        completeness_count = sum("Relevant" in response for response in model_responses)
        total = len(model_responses)
        irrelevant_count = total - hulla_count - completeness_count
        hallu_ratio = hulla_count / total if total > 0 else 0
        completeness_ratio = completeness_count / total if total > 0 else 0
        irrelevant_ratio = irrelevant_count / total if total > 0 else 0
        return hallu_ratio, completeness_ratio, irrelevant_ratio
    