def generate_checklist(query, llm_client):
    #PROMPT TEMPLATE FOR CREATING CHECKLIST
    few_shot_prompt_template = """You are an expert security analyst. Your objective is to add a "Checklist" section containing steps you would do to answer the given user query \
    For each checklist item, start with an action verb, making it clear and actionable

    **Tools**
    Below are the information tools you have access to:
    1. User Directory: query database matching user email to full name, endpoint device IPs, department, city, last login
    2. Network Traffic Database: query a database with network traffic including destination url, timestamp, source IP, destination IP, source port, destination port, bytes sent, bytes received, protocol, user
    3. Server Logs: query server logs of several central servers
    4. Threat Intelligence Database: query a database of known malicious destination IPs and destination URLs
    5. Alert Summaries: query a collection of natural language summaries of alerts, organized per user (each user has one report)
    6. Asset Management Database: query hostnames and corresponding IPs
    7. Email Security Gateway: query blocked potentially malicious emails as well as corresponding users they were sent to, and other metadata


    **Example Format**:
    Below is a format that illustrates transforming the user query into an actionable checklist.

    Example 1 SOC Query:
    An alert was triggered indicating multiple failed login attempts on the server 'DB-SERVER-01' from an external IP address. Can you investigate to determine if this is a brute force attack?

    Example 1 Checklist:
    [
        "Use 'DB-SERVER-01' to query the Asset Management Database. Return the IP address of 'DB-SERVER-01'.",
        "Use the IP address of 'DB-SERVER-01' to query the server logs. Return any patterns of failed login attempts, including repeated attempts from the same IP address, in their raw log format.",
    "Use the external IP address from the server logs to query the Threat Intelligence  Database. Return any known malicious actors.",
        "Use the returned IP addresses and patterns to query other related events or alerts. Return any indications of a broader attack pattern targeting other systems or users."
    ]

    Example 2 SOC Query:
    A phishing email was reported by an employee. The email contained a suspicious link that some users might have clicked. Can you investigate the scope of the phishing attempt and its impact?

    Example 2 Checklist:
    [
        "Use the reported phishing email to query the Email Security Gateway. Return the content of the email, including the suspicious link.",
        "Use the suspicious link to query the Email Security Gateway. Return the list of users who clicked on the link.",
        "Use the suspicious link to query the Threat Intelligence Database. Return any known associations with malicious domains."
    ]

    **Criteria**:
    - Final checklist must only include steps that are possible with the given access tools listed under Tools. Do not recommend a step which is impossible due to no access, or vague and not directly tied to one of the tools.
    - Final checklist does not need to use all provided information tools, only the ones that make sense to use
    - Final checklist is limited to 3 steps.


    **Procedure**:
    [
    "Understand the user request.",
    "Produce a checklist to accomplish the task.",
    "Format the checklist as comma separated list surrounded by square braces.",
    "Output the checklist."
    ]

    **User Query:**
    {soc_query}


    **Checklist**: 

    Please only provide the list as output."""

    formatted_prompt = few_shot_prompt_template.format(
        soc_query = query
    )

    #create checklist

    checklist=""
    for chunk in llm_client.stream([{"role":"user","content":formatted_prompt}]): 
        checklist += chunk.content


    return checklist



#EXAMPLE CHECKLISTS
# my_checklist = [
#     "Use june@domain.com to query the User Directory. Return june@domain.com's endpoint IP",
#     "Use the returned endpoint device to query the Network Traffic Database. Return any strange network traffic patterns such as unusual bytes sent and received, protocols, and URLs.",
#     "Use the returned unusual network activity to query the Threat Intelligence Database. Return any known malicious actors."
# ]

# my_checklist2 = [
#     "Use 'june@domain.com' to query the User Directory. Return the endpoint device IPs and department associated with the user.",
#     "Use the endpoint device IPs to query the Network Traffic Database. Return the destination URLs, timestamps, and protocols associated with the unusual traffic.",
#     "Use the destination URLs to query the Threat Intelligence Database. Return any associations with known malicious actors or activities."
# ]