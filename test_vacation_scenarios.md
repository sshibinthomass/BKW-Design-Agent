# Vacation Request Test Scenarios

## Current Task Status (from Task.csv)

- T-006: "Review load combinations for wind-resistant roof design" - **In Progress**
- T-010: "Develop conceptual beam alternatives for new logistics center" - **In Progress**
- All other tasks (T-001 to T-005, T-007 to T-009) are **Completed**

## Test Scenarios

### Scenario 1: Vacation Request with Open Tasks (Should be DENIED)

**User Input:** "May I go on holidays?"

**Expected AI Response:**

```
❌ VACATION REQUEST DENIED

You currently have 2 open tasks that need to be completed before vacation:

1. **T-006**: Review load combinations for wind-resistant roof design
   - Status: In Progress
   - Current Step: Updating load cases in analysis software

2. **T-010**: Develop conceptual beam alternatives for new logistics center
   - Status: In Progress
   - Current Step: Evaluating weight-to-cost ratio

**Next Steps:**
- Complete these tasks or reassign them to colleagues
- Update task status to "Completed" when finished
- Then you can request vacation again

I'll help you complete these tasks or reassign them if needed.
```

### Scenario 2: Vacation Request with All Tasks Completed (Should be APPROVED)

**User Input:** "Can I take a vacation?" (after completing all tasks)

**Expected AI Response:**

```
✅ VACATION REQUEST APPROVED

Congratulations! All your tasks are completed:
- T-001: ✅ Completed
- T-002: ✅ Completed
- T-003: ✅ Completed
- T-004: ✅ Completed
- T-005: ✅ Completed
- T-006: ✅ Completed
- T-007: ✅ Completed
- T-008: ✅ Completed
- T-009: ✅ Completed
- T-010: ✅ Completed

You've earned your vacation! 🎉

**Suggestions:**
- Set up task reminders for when you return
- Consider delegating any new incoming tasks
- Enjoy your well-deserved break!

Have a great vacation!
```

### Scenario 3: Task Completion Before Vacation

**User Input:** "I finished T-006, can I go on vacation now?"

**Expected AI Response:**

```
Great progress! Let me check your remaining tasks...

You still have 1 open task:
- **T-010**: Develop conceptual beam alternatives for new logistics center (In Progress)

Once you complete T-010, you'll be all set for vacation!

Would you like me to help you finish T-010 or reassign it to someone else?
```

## Implementation Details

The vacation logic is implemented in:

1. **CSV Task Node** (`csv_task_node.py`) - System message with vacation approval logic
2. **Return Prompt** (`return_prompt.py`) - Updated prompts for "Agentic AI" and "CSV Tasks" usecases

The system will:

1. Check task status using CSV tools
2. Identify open tasks (In Progress or Pending)
3. Deny vacation if open tasks exist
4. Approve vacation if all tasks are completed
5. Provide specific task details and next steps
