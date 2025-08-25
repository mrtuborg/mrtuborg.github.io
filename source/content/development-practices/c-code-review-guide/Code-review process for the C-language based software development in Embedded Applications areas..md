---
{"publish":true,"created":"2024-06-23T13:30:04.000+02:00","modified":"2025-08-25T19:36:09.479+02:00","cssclasses":""}
---

# Preamble
The code-review process typically involves two key players: the "Author," who proposes changes to the codebase, and the "Reviewer," who is either assigned the task or volunteers for it. The primary responsibility of the "Author" is to demonstrate that the provided code adheres to the internal rules and agreements of the development team responsible for the target codebase. On the other hand, the main focus of the "Reviewer" is to identify any deviations from these rules or agreements within the development team. This guide aims to assist both parties in efficiently and smoothly carrying out their respective roles towards the common objective of enhancing the codebase with the proposed changeset.

# The workflow.
The workflow described can be broken down into four phases as follows:
1. Precommit-review:
	- The author reviews their own code before submitting it for review by others.
	- The goal is to remove any obstacles that could make the reviewer's job difficult.
2. Postcommit-review:
	- The reviewer goes through the code submitted by the author in several passes, looking for deviations from different perspectives on each pass.
	- The reviewer provides feedback to the author, highlighting the deviations found and, probably, suggesting improvements.
3. Proposion fix:
	- The author takes the feedback provided by the reviewer and works on improving the proposed code based on the identified deviations.
4. Code changeset acceptance:
	- Once the author has addressed all the identified deviations and the reviewer is satisfied with the proposed fixes, the changeset is ready for acceptance and merging into the codebase.
	- The reviewer ensures that the proposed changes align with the goals of the review process and meet the required quality standards before accepting the code changeset.

# Precommit-review phase checklist.
1. Have you run linting tools?
2. Ensure the code complies with the project's coding standards.
	- Check for adherence to naming conventions.
	- Validate the use of data types and structures.
	- Confirm that the code formatting is consistent throughout.
3. Verify that the code meets the initial requirements.
	- Compare the implementation with the specification document.
	- Ensure that all the functionalities are implemented as intended.
4. Are your comments clear and grammatical?
	- If a comment is or is meant to be a complete sentence, capitalize it, punctuate it, and re-read it to make sure it parses!
	- If your editor has a spell-checker for strings and comments, did you run it?
	- If code is commented, could the code be rewritten so that the comments aren't necessary?
5. Did you document your API? Did you comment your complexity?
	- Every nontrivial public symbol must have a Doxygen-formatted comment.
	-  If you are uncertain of your formatting, consider [](https://drake.mit.edu/documentation_instructions.html)[generating the Doxygen](https://drake.mit.edu/documentation_instructions.html) and checking how it looks in a browser.
	- Only use Doxygen comments (/// or /** */) on published APIs (public or protected classes and methods). Code with private access or declared in .cc files should _not_ use the Doxygen format.
	- Ensure that complex algorithms are explained.
	- Anything in your code that confuses you or makes you read it twice to understand its workings should have an implementation comment.
	- Review the presence of a README file for module-level explanations.
6. If you changed logic somewhere did you update the UML/Sequence Diagram?
7. If you changed set of entities in the solution did you update UML/Class Diagram?

# Precommit-review phase.
This phase is executed by the designated Reviewer and includes the following six passes:
 **A**. Assignment compliance review
 **B**. Solution design review
 **C**. Solution correctness review
 **D**. Solution efficiency review
 **E**. Solution robustness review

## A. Assignment compliance review checklist
1. Proposed change-set has documented and needed diagrams are updated
2. Change-set passed hardware independent (unit-testing) and hardware dependent tests (integration-testing).
3. Change-set is atomic and has no more than 500 lines for review.
4. Code was built with predefined rules for the clang-formatter utility

## B. Solution design review checklist

1. Assess the code for proper architectural adherence. Evaluate the use of design patterns.
	1. Ensure modularity and separation of concerns.
	2. Verify that the code is robust and extendable for future enhancements.
	3. Verify that the approved architecture/design is followed throughout the application (If there is none, consider putting it in place). If there are any design changes required, ensure that these are documented, baselined and approved before implementing them in the existing code.
2. Is the program sufficiently modular? Will modifications to one part of the program require modifications to others?
	1. The ‘<’ and ‘>’ symbols are used to include system header files.  The system header files are listed in alphabetical order.
	2. Double quotation is used for the inclusion of all non-system header files. The nonsystem header files are listed in alphabetical order.
	3. Absolute or relative paths upward are not used in the "include" to point to header file locations.
	4. Header files contain preprocessor directives preventing multiple inclusions.
3. Variable names are descriptive
4. Function names are descriptive
5. Check that each function does one thing and has a single responsibility.
6. All methods serve a limited and clear purpose (follows DRY principle). Functions are reused wherever applicable and written in such a way that they can be re-used in the future implementations. There is no duplication of code. Logics make use of general functions without ambiguity.
7. Is There Code Duplication? Use specialized tools to detect copy-pasting trough the codebase
8. Commented-out code should be removed.
9. Code that isn’t part of the build, or doesn’t have unit tests is not presented in changeset
10. Don’t include files with only whitespace diffs in your pull request (unless of course the purpose of the changes is whitespace fixes).
11. There is no dead code
12. There are no empty blocks of code or unused variables.

## C. Solution correctness review
To check that the logic of the function is correct and properly implemented, you can follow these steps:
1. Understand the Requirements: Ensure a clear understanding of what the function is supposed to do based on the given requirements or specifications.
2. Review the Algorithm: Understand the algorithm used within the function.
3. Consider Boundary Cases: Test the function with boundary cases and edge cases.
4. Verify the Base Case: Confirm that the base case of the algorithm is properly handled.
5. Check against  [[development-practices/c-code-review-guide/Most common issues and anti-patterns in C-language]]
6. [[development-practices/c-code-review-guide/Check for suboptimal memory or data structures management]]
7. [[development-practices/c-code-review-guide/Multithreaded C Code and Interrupts]]
8. [[development-practices/c-code-review-guide/Undefined behaviour]]

## D. Solution efficiency review

1. Analyze the code for performance optimization.
	1. The code, where speed is a priority, has been optimized to run as fast as possible.
	2. Validate function length; functions should be concise.
	3. Is the code the minimal set of what you want?
	4. Identify unnecessary computations.
	5. Check for the efficient use of memory and resources.
	2. Unnecessary code is avoided in loops. Blocks of code inside loops are as small as possible
	3. Review for potential bottlenecks in execution speed.
	4. Frequently used variables are qualified with the “register” keyword.
2. Validate the code against real-time requirements.
	1. Check for timing constraints and deadlines.
	2. Review synchronization mechanisms and concurrency.
	3. Ensure that time-critical sections are properly optimized.
3. Reading complexity
4. Writing overly complex code that is hard to understand or maintain.
5. Check against practices and look for most common issues and anti-patters in the provided code for the review
6. [[development-practices/c-code-review-guide/Efficient Data Structures usage]]
7. [[development-practices/c-code-review-guide/Specific language keywords]]

