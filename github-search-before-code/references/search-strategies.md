# GitHub Search Strategy Guide

This document provides strategies for effectively searching GitHub and analyzing results across different scenarios.

## Extracting Search Keywords

### General Principles

1. **Prioritize Core Functional Terms**: Extract the core technical names of functionality
   - ✅ Good: "FFT", "Modbus", "PID controller"
   - ❌ Poor: "calculate frequency", "communication protocol"

2. **Combine Keywords**: Core functionality + application scenario
   - Examples: "FFT embedded", "Modbus RTU C", "PID control motor"

3. **Avoid Overly Specific Project Terminology**
   - ✅ Good: "three-phase power metering"
   - ❌ Poor: "RN7326 DLT645 three-phase MCB"

### Keyword Strategies for Different Function Types

| Function Type | Keyword Strategy | Examples |
|---------------|------------------|----------|
| **Algorithm Implementation** | Algorithm name + "implementation" / "algorithm" | "FFT algorithm C", "Kalman filter embedded" |
| **Communication Protocol** | Protocol name + variant + language | "Modbus RTU C", "DLT645 protocol", "UART protocol parser" |
| **Hardware Driver** | Chip/peripheral name + "driver" | "SPI flash driver", "RTC driver embedded" |
| **Mathematical Operations** | Operation name + "fixed point" / "embedded" | "sine cosine fixed point", "square root integer" |
| **Data Processing** | Processing method + data type | "moving average filter", "circular buffer C" |
| **Signal Processing** | Signal processing technique + domain | "harmonic analysis power", "phase detection" |
| **State Machine/Flow** | State machine type + application | "finite state machine C", "event driven framework" |

## Search Strategy

### Two-Phase Search

1. **Phase 1: Repository Search** (repo search)
   - Purpose: Find high-quality complete implementations
   - Use cases: Need overall architecture reference, complete functional modules
   - Command: `python3 github_search.py repo "<keywords>" [language]`

2. **Phase 2: Code Search** (code search) - Optional
   - Purpose: Find specific code snippets and implementation details
   - Use cases: Phase 1 didn't yield satisfactory results, or need more specific implementation examples
   - Command: `python3 github_search.py code "<keywords>" [language]`

### Language Filtering Recommendations

For embedded projects:

1. **First priority**: No language restriction (leave empty) - get the broadest results
2. **Second choice**: C language - most suitable for direct embedded porting
3. **Third choice**: C++ - some algorithms can be referenced and rewritten in C

For algorithm research:
- No language restriction - focus on understanding algorithm concepts rather than specific implementation

## Result Analysis and Filtering

### Quick Filtering Criteria

Evaluate each result in the following order:

1. **Star Count** (primary metric)
   - ⭐ > 100: High quality, worth deep investigation
   - ⭐ 20-100: Medium quality, can reference
   - ⭐ < 20: Use cautiously, needs careful verification

2. **Description Match**
   - Does the repository description highly relate to requirements
   - Does it clearly state supported functionality

3. **Last Updated**
   - Updated within 2 years: Active project
   - 2-5 years: Stable project, likely still usable
   - > 5 years: Technology may be outdated, use cautiously

4. **License**
   - MIT/BSD/Apache: Free to use and modify
   - GPL: Note open source obligations
   - No license/Unknown: Use cautiously

5. **Language Match**
   - C/C++: Most suitable for embedded projects
   - Python/Java etc.: Need to understand algorithm then rewrite

### In-Depth Analysis Process

For filtered candidate repositories (typically top 3-5):

1. **Read README**
   - Use WebFetch or Read tools to obtain README content
   - Confirm feature list, usage examples, dependencies

2. **Check Code Structure**
   - Clone or browse main source files
   - Assess code complexity and readability
   - Check for good modular design

3. **Review Examples and Tests**
   - Are usage examples provided
   - Is there test code (indicates code quality)

4. **Evaluate Porting Difficulty**
   - Number of dependencies (fewer is better)
   - Proportion of platform-specific code
   - Lines of code (overly large implementations may not suit small embedded projects)

### Usability Assessment

Consider "usable" if meeting any of the following conditions:

✅ **Directly Usable**:
- Pure C implementation, no external dependencies
- Concise code (< 500 lines)
- Provides clear API interface
- Has usage examples

✅ **Requires Minor Modifications**:
- C++ implementation but clear algorithm
- Few platform dependencies (like standard library functions)
- Clear code structure, easy to extract core logic

⚠️ **Reference Only**:
- Different language but clear algorithm concepts
- Complex code but detailed documentation
- Requires significant rewriting but provides good design ideas

❌ **Not Usable**:
- Messy code, lacks comments
- Heavy dependency on specific platform or framework
- Incompatible license

## How to Use Reference Implementations

### After Finding a Usable Implementation

1. **Don't directly copy-paste entire repository code**
   - Understand core algorithm and design concepts
   - Extract necessary functions and data structures
   - Adapt and simplify according to project requirements

2. **Preserve Reference Source**
   - Note reference source in code comments
   - Record original repository URL
   - Comply with original license requirements

3. **Adapt Rather Than Copy**
   - Adapt to project's code style
   - Simplify unnecessary features
   - Optimize memory and performance for embedded environment

### Handling Cases Without Suitable Implementation

If no suitable reference found after searching:

1. **Adjust Search Keywords**: Use more generic or more specific terms to search again
2. **Consider Higher-Level Algorithm Concepts**: For example, if "three-phase harmonic analysis" not found, search for "FFT frequency domain analysis"
3. **Split Functionality Search**: Break complex functionality into multiple sub-functions and search separately
4. **Use WebSearch**: Search academic papers, technical blogs to obtain algorithm principles

## Special Notes for Scenario 2: Repeated Debugging Without Success

When users repeatedly report unresolved issues, search strategy should:

1. **Extract Core Functionality of Current Implementation**: Clarify what we're trying to implement
2. **Search for Standard Implementations of Same Functionality**: Look for industry-recognized best practices
3. **Comparative Analysis**:
   - Is our implementation approach correct
   - Are there missing critical steps
   - Is there a simpler, more reliable implementation method
4. **Reference-Based Improvement**: Adjust strategy based on reference implementations

The purpose of this scenario is not to replace the entire implementation, but to verify and correct the implementation approach.
