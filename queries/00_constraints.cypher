// Run explicitly in Neo4j Browser after startup; mounting this directory does not execute it.
CREATE CONSTRAINT researcher_id IF NOT EXISTS
FOR (n:Researcher) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT organization_id IF NOT EXISTS
FOR (n:Organization) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT paper_id IF NOT EXISTS
FOR (n:Paper) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT topic_id IF NOT EXISTS
FOR (n:Topic) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT venue_id IF NOT EXISTS
FOR (n:Venue) REQUIRE n.id IS UNIQUE;
