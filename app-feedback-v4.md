Now let us focus on two sections of the website:
1. The topic section
2. The feed section

Right now, the topic section is arranged in such a way that there is very little information available. There are key words, yes, but there is very little information available about what this key word is about.

So something about the relevance of the keyword should be shown in the topic section itself, so I know that I should click it to read more about it.

I like that in the topics you have mentioned the date and also you have mentioned the number of items present within that topic. If there is one repo and one subreddit article present, there are two icons corresponding to it. That is very good.
Please keep it.

The way in which the keywords are used is very useless at the moment. For example, Microsoft is a keyword. From that, I don't understand anything. Why should I just click something because I see the word Microsoft? I click something if I see the keyword
Scrapy

So, based on recency and popularity, I want to have a score system.

Both are important to me. The news has to be recent, so recency I can define based on my filter. If I say one month, that one month is the timeline that I am interested in following, and then basically I need you to show big items based on its relevance and popularity.

The topic should be in such a way that whatever is displayed in front of me should be extremely relevant for me in terms of what is going on in the AI world right now.

One more thing that I want to implement is currently you have only fetched the news from yesterday. I want you to fetch the relevant news from the last one month.

So that I have one month's worth of data in my database 


reddit → add more relevant subreddits, do not show all posts [recency + popularity] arxiv → organize based on recent traction or popularity [recency + popularity] github - trending repos based on star rating, forks, date [recency + popularity]

Currently, the way you are showing me, arXiv, Reddit, and GitHub are in a column, so I have to scroll through every single arXiv before I reach GitHub, or every single Reddit post before I reach GitHub in the Feed page.

One thing I want to implement is that if we are tetching relevant data from the last one month, last six months, or last one year, there should be a different way to filter information instead of scraping the entire subreddits or instead of scraping the entire data from the internet.

Sources: you should add some other sources which are already existing aggregators, like other websites which aggregate such news, so that we can add here.

I also want you to give me a list of other subreddits which you can add to track.

But it should not happen that you are showing me a lot of information and overwhelming me. I should be able to set my preferences to see X amount of information with so much relevance and such and such keywords from such and such topics.

In order to make this website completely useful, a little bit of overhaul has to be there.

In the paper section, I can see a lot of papers that are being populated from two days back or one day back, but that is not the right thing to do, because I don't want to see every single paper. I want to see only the most relevant papers.

In the topic section, I am not able to read the full subtitle associated with each topic because the subtitle is getting clipped.

Also, the title is too short, and it's not adding too much value in the topic section; that also needs to be fixed.

For example, the topic like GPT-5 or mixture of experts or fine-tuning. These are very vague topics. It does not make any sense for me to read something like fine-tuning and click on it, because fine-tuning is a very broad topic. The topic and the sub-topic, which is listed inside each individual card, should be useful to me.

In the GitHub, the total number of stars and the stars achieved today should be displayed as separate two boxes inside the individual cards. Right now, it is being displayed along with the subtitle, and because of that reason, if the subtitle length is long, the star is also not getting visible on the page. This issue is there in the feed section.

In the topic section, I noticed that some of the items are being repeated That should never happen.
What you can do instead is, for the same item, if multiple tags are appropriate, you can add multiple tags. 

I want you to fetch items since the last one month or last thirty days, and for each day only show the relevant item.

Otherwise, if you are showing so many things from one single day, it will simply be overwhelming, and a lot of the items that you are showing will be not useful.

Also, when you are showing me repositories or papers, you show the date and time. Is that the date and time during which you have added it to my feed? That is not relevant. What is relevant is when the original item was created. If the paper was published on a particular date, that is more important to me. I don't care when it was added to my feed.

in the feed section, in the "all" tab, there should be interleaving of the feed from different sources.
I want to see only the top 10 items from each section or source per day - something like this should be available in the settings

There should be save option in the settings tab

Don't make the site overwhelming with info
LLM smartness in producing concise version of lets say what happened in the last 1 week or 1 month or so
So many arxiv papers are being displayed. What is the logic? only papers that are gaining traction need to displayed
I don't want to see every single Subreddit article displayed here because that will make my feed crowded.
On the field section, I can see that a lot of articles are being displayed.
I can't see the number of upvotes or comments easily without opening - some LLM intelligence should be there

make sure to optimise the codebase and the website and make it efficient, optimised and use the best programming principles 