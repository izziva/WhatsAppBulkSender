Title: Add functionality to send messages every X seconds

## Feature Request

### Description
Add the functionality to send messages with a configurable delay of X seconds.

### Details
- Define X in the `config.py` file with a default value of 15 seconds.
- Update the sending logic to consider this interval.

### Benefits
- Helps regulate and control message-sending speed.

### Suggested Approach
1. Introduce a new variable `MESSAGE_DELAY` in `config.py` and set it to 15 by default.
2. Update the sending logic to include a delay based on this variable.

### References
Provide real examples or scenarios where this will be beneficial.

Let me know if more details are needed!