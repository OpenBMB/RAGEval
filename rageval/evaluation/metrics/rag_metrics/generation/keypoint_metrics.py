from dataclasses import dataclass
from typing import List
from openai import OpenAI
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
Key Point Evaluation:
"""

@dataclass
class KEYPOINT_METRICS:
    name: str = "keypoint_metrics"

    def __init__(self, use_openai = False):
        # 初始化任何必要的属性
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set")
        self.client = OpenAI(
            api_key= self.openai_api_key,
        )
        self.use_openai = use_openai

    def __call__(self, doc, language="zh") -> float:
        question = doc["query"]["content"]
        prediction = doc["prediction"]["content"]
        key_points = doc["ground_truth"]["keypoints"]

        resp_2_kp = {}
        key_points_list = self._parse_key_points(key_points)
        responses = []
        origin_responses = []
        for kp in key_points_list:
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

    def _handle_key_point(self, question, prediction, key_point, language):
        """
        为单个关键点生成提示并调用chat_sync。
        """
        prompt = self._create_prompt(question, prediction, key_point, language)
        if self.use_openai:
            messages = [{"role": "user", "content": prompt}]
            #print("messages:", messages)
            response = self.client.chat.completions.create(
                messages = messages,
                model = "gpt-4o",
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

    def _calculate_ratio(self, model_responses) -> float:
        """
        根据模型的响应计算Wrong所占的比例，数值越高说明幻觉现象越严重，说明被测试系统性能越低（仅幻觉鲁棒性）。
        """
        hulla_count = sum("Wrong" in response for response in model_responses)
        completeness_count = sum("Relevant" in response for response in model_responses)
        irrelevant_count = sum("Irrelevant" in response for response in model_responses)
        total = len(model_responses)
        hallu_ratio = hulla_count / total if total > 0 else 0
        completeness_ratio = completeness_count / total if total > 0 else 0
        irrelevant_ratio = irrelevant_count / total if total > 0 else 0
        return hallu_ratio, completeness_ratio, irrelevant_ratio