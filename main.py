"""
- should I pull data into a separate db or pull it on-demand?
    -> 1) we want a standard schema and 2) we won't always be able to query on-demand, so probably unified db
    -> I'm thinking some sort of SQL too bc it's time series and we want nice queries over it

Design:
- define class to interact with db / define schema
- define abstract class to fetch from source, subclass for each source, these can be batch-fetched with a simple script
    - fetchers can also perform transforms. Can have multiple fetchers with same underlying source, but they're grabbing different structured data out.
      ex. multiple LLM parsers on Obsidian daily notes
- wrapper textual app that renders a list of visualizations
    - interface for a visualization: takes in the database class, outputs a textual component


Sources:
- ActivityWatch
- Hevy
- Strava
- Obsidian + LLM (later)


Prototype dashboard goal:

     School    ATA   Fitness
Mon: [=====] [=====] [==]
Tue:
Wed:
.
.
.


Next:
- fitness over time
- habit heatmap
- goal / todo parsing
- sleep
- mood/energy/focus with randomized pings
- books / blog posts
-
"""
