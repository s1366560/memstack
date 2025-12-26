# Fix: Deep Search Graph Visualization Bug

## Issue Analysis
The user reported that the Deep Search results and the Graph are not directly related, with the Graph always showing all nodes.
- **Root Cause:** The `CytoscapeGraph` component uses `cyRef.current.json({ elements })` to update the graph. In Cytoscape.js, this method often behaves as a merge/diff operation rather than a full replacement. Consequently, when switching from the "Full Graph" (initial state) to a "Subgraph" (search results), the existing nodes from the full graph are not removed, causing the visualization to display the union of both (i.e., the full graph).
- **Correct Behavior:** When `subgraphNodeIds` are provided, the graph should strictly display only the returned subgraph elements.

## Proposed Changes

### Frontend: `web/src/components/CytoscapeGraph.tsx`
1.  **Explicitly Clear Graph:** Modify `loadGraphData` to call `cyRef.current.elements().remove()` before updating the graph with new data.
2.  **Use `cy.add()`:** Instead of `cy.json({ elements })`, use `cy.add(elements)` after clearing to ensure a clean state.

```typescript
// Inside loadGraphData
cyRef.current.elements().remove() // Clear existing graph
cyRef.current.add(elements)       // Add new elements
cyRef.current.layout(layoutOptions).run()
```

## Verification
- After this change, performing a search should trigger `getSubgraph`.
- The graph component will clear all old nodes.
- Only the nodes returned by `getSubgraph` (search results + 1-hop neighbors) will be rendered.
- Toggling "Show Full Graph" (if implemented in UI) or clearing search will reload the full graph, which will again clear and fill the canvas.

This fix addresses the "Graph always shows all nodes" issue directly.