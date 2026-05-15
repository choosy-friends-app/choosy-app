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
