I will enhance the graph display capabilities by updating the `GraphitiService` to leverage the existing `Graphiti` client and include community nodes in the visualization, as seen in Zep Playground.

### Technical Implementation

#### 1. Optimize Graph Data Retrieval
- Modify `server/services/graphiti_service.py` to remove the direct usage of `neo4j.AsyncGraphDatabase`.
- Instead, reuse the existing connection via `self.client.driver.execute_query`. This aligns with the requirement to use the project's `graphiti` capabilities and avoids creating redundant database connections.

#### 2. Enhance Graph Visualization Data
- Update the Cypher query in `get_graph_data` to include `Community` nodes:
  ```cypher
  MATCH (n)
  WHERE 'Entity' IN labels(n) OR 'Episodic' IN labels(n) OR 'Community' IN labels(n)
  OPTIONAL MATCH (n)-[r]->(m)
  WHERE ('Entity' IN labels(m) OR 'Episodic' IN labels(m) OR 'Community' IN labels(m))
  ...
  ```
- This enables the frontend to display community clusters, providing a higher-level view of the knowledge graph similar to Zep Playground.

#### 3. Verification
- I will verify the changes by ensuring the `get_graph_data` method returns the correct structure (nodes and edges) including any available community nodes.
- The existing frontend `GraphView.tsx` should be able to render the additional nodes automatically as it renders generic nodes and edges.
