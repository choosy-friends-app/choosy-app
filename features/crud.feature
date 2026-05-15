Feature: Plan CRUD
  As an authenticated Choosy user
  I want to manage only my own plans
  So that group decisions remain trustworthy

  Background:
    Given the following users exist:
      | username | password    |
      | alice    | testpass123 |
      | bob      | testpass123 |
    And Alice owns a group with an open proposal
    And Bob owns a group with an open proposal

  Scenario: Happy path for creating, updating, and deleting a plan
    Given I am logged in as "alice"
    When I create a plan titled "Tapas night"
    Then I should see that the plan "Tapas night" exists
    When I update the plan "Tapas night" to "Museum brunch"
    Then I should see that the plan "Museum brunch" exists
    When I delete the plan "Museum brunch"
    Then I should see that the plan "Museum brunch" no longer exists

  Scenario: Missing required data keeps the plan form open
    Given I am logged in as "alice"
    When I submit the plan form without a title
    Then the plan should not be created
    And the plan form should show a validation error

  Scenario: Invalid numeric data keeps the plan form open
    Given I am logged in as "alice"
    When I submit the plan form with an invalid price
    Then the plan should not be created
    And the plan form should show a validation error

  Scenario: A user cannot edit another user's plan
    Given Bob has a plan titled "Private bowling"
    And I am logged in as "alice"
    When I try to edit Bob's plan
    Then the request should be forbidden
    And Bob's plan title should still be "Private bowling"

  Scenario: A user cannot delete another user's plan
    Given Bob has a plan titled "Private dinner"
    And I am logged in as "alice"
    When I try to delete Bob's plan
    Then the request should be forbidden
    And I should see that the plan "Private dinner" exists

  Scenario: Happy path for creating, updating, and deleting a group
    Given I am logged in as "alice"
    When I create a group named "Cinema Crew"
    Then I should see that the group "Cinema Crew" exists
    When I update the group "Cinema Crew" to "Cinema Nights"
    Then I should see that the group "Cinema Nights" exists
    When I delete the group "Cinema Nights"
    Then I should see that the group "Cinema Nights" no longer exists

  Scenario: Missing required data keeps the group form open
    Given I am logged in as "alice"
    When I submit the group form without a name
    Then the group should not be created
    And the plan form should show a validation error

  Scenario: A user cannot edit another user's group
    Given Bob has a group named "Bob Secret Group"
    And I am logged in as "alice"
    When I try to edit Bob's group
    Then the request should be forbidden
    And Bob's group name should still be "Bob Secret Group"

  Scenario: A user cannot delete another user's group
    Given Bob has a group named "Bob Delete Group"
    And I am logged in as "alice"
    When I try to delete Bob's group
    Then the request should be forbidden
    And I should see that the group "Bob Delete Group" exists

  Scenario: Happy path for creating, updating, and deleting a proposal
    Given Alice owns an extra group named "Alice Proposals Group" without proposals
    And I am logged in as "alice"
    When I create a proposal titled "Friday Brainstorm" for group "Alice Proposals Group"
    Then I should see that the proposal "Friday Brainstorm" exists
    When I update the proposal "Friday Brainstorm" to "Saturday Brainstorm"
    Then I should see that the proposal "Saturday Brainstorm" exists
    When I delete the proposal "Saturday Brainstorm"
    Then I should see that the proposal "Saturday Brainstorm" no longer exists

  Scenario: Missing required data keeps the proposal form open
    Given Alice owns an extra group named "Alice Validation Group" without proposals
    And I am logged in as "alice"
    When I submit the proposal form without a title for group "Alice Validation Group"
    Then the proposal should not be created
    And the plan form should show a validation error

  Scenario: A user cannot edit another user's proposal
    Given Bob has a proposal titled "Bob Secret Proposal"
    And I am logged in as "alice"
    When I try to edit Bob's proposal
    Then the request should be forbidden
    And Bob's proposal title should still be "Bob Secret Proposal"

  Scenario: A user cannot delete another user's proposal
    Given Bob has a proposal titled "Bob Delete Proposal"
    And I am logged in as "alice"
    When I try to delete Bob's proposal
    Then the request should be forbidden
    And I should see that the proposal "Bob Delete Proposal" exists
