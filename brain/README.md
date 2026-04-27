# Brain

Central command for task management, prioritization, and agent coordination.

## Files

- `eisenhower.md` - Main task prioritization (Eisenhower Matrix)
- `agents.md` - Registry of available agents and their capabilities
- `companies.md` - Companies, products, ownership, domains (create as needed)
- `credentials.yaml` - Sensitive credentials (git-ignored, create as needed)

## Workflow

When a task is identified:

1. **Add to project file** (e.g., `project/notes.md`)
   - Context, details, discussion history

2. **Add to Eisenhower Matrix** (`brain/eisenhower.md`)
   - Categorize: Q1 (Do), Q2 (Schedule), Q3 (Delegate), Q4 (Delete)
   - Assign **Owner** (user or agent)
   - Link to project for reference

3. **Execute based on quadrant**
   - Q1: Do immediately (owner executes)
   - Q2: Schedule time block
   - Q3: Delegate to agent → track in "Waiting For"
   - Q4: Remove

4. **Track delegated tasks**
   - Move to "Waiting For" section
   - Periodically request status reports from agents
   - Update when complete

5. **Mark complete** in both places

## Review Cadence

- **Daily:** Check Q1 (urgent+important), check "Waiting For"
- **Weekly:** Review Q2 (schedule important work), request agent reports
- **Monthly:** Audit Q3/Q4 (delegation, elimination), review agent capabilities
