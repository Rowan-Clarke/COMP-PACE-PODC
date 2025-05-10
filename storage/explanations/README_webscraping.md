# Webscraping test - updated 15/4/25
 Hi everyone Dylan here,
 I've created this folder to upload current webscraping file I've been using to be used as information to feed the chatbot.

 At some stage (hopefully soon) the data will need to be stored in a mostly static location (vector database or potentially sql), reason being is having to webscrap everytime the chatbot is called will most likely result in unneccessary resource usage, longer response times, unpredictability with answers, among other problems.
 I'm attempting to figure the best solution, in line with financial cost and efficiency. But for now, I'm updating this procedure to account for different website type (dynamic, static - html, javascript, pdf, etc).

 Right now 15/4/25 - html sites tend to be a bit strange, and a particular section of the html 'layer' needs to be specified in order for the webscraper to work. For example, the website 'aussiedeafkids.org.au' has a main content layer called 'entry-content', whereas other sites may have 'content', 'article-body', among others. So I'm trying to work around these cases to fit all solutions, and reduce the amount of manual intervention.
