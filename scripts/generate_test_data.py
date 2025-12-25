#!/usr/bin/env python3
"""
Generate test data for MemStack application.

This script creates realistic test data including:
- Tenants (workspaces)
- Projects
- Episodes (conversations, interactions, events)
- Entities and relationships will be automatically extracted by Graphiti
"""

import asyncio
import argparse
import logging
import random
from datetime import datetime, timedelta
from typing import Optional
import uuid

import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestDataGenerator:
    """Test data generator for MemStack."""

    # Sample realistic data templates
    EPISODE_TEMPLATES = [
        # User preference episodes
        "User {name} prefers {preference} mode in the application settings.",
        "When {name} logs in, they always set the theme to {preference}.",
        "{name} mentioned that they like {preference} color scheme better.",
        "The user {name} changed their display preference to {preference}.",
        "{name}'s profile shows preference for {preference} interface.",
        # Task and activity episodes
        "{name} completed the task '{task_name}' in the {project} project.",
        "User {name} created a new document called '{document_name}'.",
        "{name} reviewed the pull request for {feature_name}.",
        "Meeting scheduled: {name} to discuss {topic} with {team}.",
        "{name} assigned {assignee} to work on {task_name}.",
        # Product usage episodes
        "{name} used the {feature} feature to analyze {data_type}.",
        "The {feature} tool was accessed by {name} for data processing.",
        "{name} exported results using the {feature} module.",
        "User {name} configured {feature} with specific parameters.",
        # Support and interaction episodes
        "{name} reported an issue with {component}: {issue_description}.",
        "Support ticket created by {name} regarding {feature}.",
        "{name} requested help with {task} in the {project} workspace.",
        "{name} gave feedback that the {feature} should be improved.",
        # Learning and training episodes
        "{name} completed the training module on {topic}.",
        "New user {name} attended the onboarding session for {project}.",
        "{name} studied the documentation about {feature}.",
        "{name} asked questions about {topic} during the team meeting.",
    ]

    NAMES = [
        "Alice Johnson",
        "Bob Smith",
        "Carol Williams",
        "David Brown",
        "Emma Davis",
        "Frank Miller",
        "Grace Wilson",
        "Henry Taylor",
        "Ivy Anderson",
        "Jack Thomas",
        "Kate Martinez",
        "Liam Garcia",
        "Mia Rodriguez",
        "Noah Lee",
        "Olivia Clark",
        "Paul Walker",
        "Quinn Hall",
        "Rachel Allen",
        "Sam Young",
        "Tina King",
    ]

    PREFERENCES = [
        "dark",
        "light",
        "compact",
        "expanded",
        "detailed",
        "simplified",
        "grid view",
        "list view",
        "sidebar navigation",
        "top navigation",
    ]

    TASKS = [
        "data analysis",
        "report generation",
        "code review",
        "documentation",
        "bug fixing",
        "feature development",
        "testing",
        "deployment",
        "database migration",
        "API integration",
        "UI design",
        "performance optimization",
    ]

    DOCUMENTS = [
        "Q4 Financial Report",
        "Product Roadmap 2024",
        "User Research Summary",
        "Technical Architecture Document",
        "Marketing Strategy Presentation",
        "Sales Performance Dashboard",
        "Customer Feedback Analysis",
        "Security Audit Report",
        "Compliance Documentation",
        "Team Handbook",
    ]

    FEATURES = [
        "knowledge graph",
        "semantic search",
        "entity extraction",
        "relationship analysis",
        "community detection",
        "data export",
        "memory visualization",
        "natural language query",
        "auto-tagging",
        "recommendation engine",
        "anomaly detection",
        "trend analysis",
    ]

    PROJECTS = [
        "Alpha Research",
        "Beta Development",
        "Gamma Analytics",
        "Delta Operations",
        "Epsilon Services",
    ]

    TOPICS = [
        "machine learning",
        "data science",
        "cloud infrastructure",
        "cybersecurity",
        "user experience",
        "product strategy",
        "customer success",
        "sales techniques",
        "marketing automation",
        "agile methodology",
        "devops practices",
        "API design",
    ]

    TEAMS = [
        "engineering team",
        "product team",
        "marketing team",
        "sales team",
        "support team",
        "data team",
        "research team",
    ]

    COMPONENTS = [
        "login page",
        "dashboard",
        "search functionality",
        "export feature",
        "notification system",
        "user profile",
        "settings panel",
        "report generator",
        "data visualization",
        "API endpoint",
    ]

    ISSUES = [
        "slow loading time",
        "authentication failure",
        "data sync issue",
        "display bug",
        "error handling problem",
        "access control issue",
        "notification delay",
        "search inaccuracy",
        "export format error",
    ]

    def __init__(
        self,
        base_url: str = "http://localhost:8000/api/v1",
        api_key: Optional[str] = None,
        tenant_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        """
        Initialize the test data generator.

        Args:
            base_url: Base URL of the API
            api_key: API key for authentication
            tenant_id: Tenant ID to use (will create if None)
            project_id: Project ID to use (will create if None)
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.tenant_id = tenant_id
        self.project_id = project_id
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=60.0,  # Increased timeout for Graphiti processing
        )
        return self

    async def __aexit__(self, *args):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()

    def _generate_episode_content(self) -> str:
        """Generate a random episode content."""
        template = random.choice(self.EPISODE_TEMPLATES)

        # Build format dict with all possible values
        format_values = {
            "name": random.choice(self.NAMES),
            "preference": random.choice(self.PREFERENCES),
            "task": random.choice(self.TASKS),
            "task_name": random.choice(self.TASKS),
            "document_name": random.choice(self.DOCUMENTS),
            "feature": random.choice(self.FEATURES),
            "project": random.choice(self.PROJECTS),
            "topic": random.choice(self.TOPICS),
            "team": random.choice(self.TEAMS),
            "component": random.choice(self.COMPONENTS),
            "issue_description": random.choice(self.ISSUES),
            "feature_name": random.choice(self.FEATURES),
            "assignee": random.choice(self.NAMES),
            "data_type": random.choice(
                ["user data", "sales data", "product data", "analytics data"]
            ),
        }

        # Use safe formatting that only replaces available placeholders
        try:
            return template.format(**format_values)
        except KeyError as e:
            # Fallback: if template has unexpected placeholders, return a simple one
            logger.warning(f"Template formatting error: {e}, using fallback")
            return f"User {format_values['name']} performed an action in the system."

    async def create_tenant(self, name: str, description: str = "") -> dict:
        """
        Create a new tenant/workspace.

        Args:
            name: Tenant name
            description: Tenant description

        Returns:
            Created tenant data
        """
        logger.info(f"Creating tenant: {name}")

        # Note: This endpoint may not exist, adjust based on your API
        response = await self.client.post(
            "/tenants/",
            json={"name": name, "description": description or f"Test workspace: {name}"},
        )
        response.raise_for_status()
        data = response.json()
        logger.info(f"Created tenant with ID: {data.get('id')}")
        return data

    async def create_project(self, tenant_id: str, name: str, description: str = "") -> dict:
        """
        Create a new project.

        Args:
            tenant_id: Tenant ID
            name: Project name
            description: Project description

        Returns:
            Created project data
        """
        logger.info(f"Creating project: {name}")

        # Note: This endpoint may not exist, adjust based on your API
        response = await self.client.post(
            "/projects/",
            json={
                "tenant_id": tenant_id,
                "name": name,
                "description": description or f"Test project: {name}",
            },
        )
        response.raise_for_status()
        data = response.json()
        logger.info(f"Created project with ID: {data.get('id')}")
        return data

    async def create_episode(
        self,
        content: str,
        name: Optional[str] = None,
        source_type: str = "text",
        metadata: Optional[dict] = None,
        valid_at: Optional[datetime] = None,
    ) -> dict:
        """
        Create a new episode.

        Args:
            content: Episode content
            name: Optional episode name
            source_type: Source type (text, json, document, api)
            metadata: Optional metadata
            valid_at: Optional valid datetime

        Returns:
            Created episode response
        """
        episode_data = {
            "content": content,
            "source_type": source_type,
        }

        if name:
            episode_data["name"] = name
        if metadata:
            episode_data["metadata"] = metadata
        if valid_at:
            episode_data["valid_at"] = valid_at.isoformat()
        if self.tenant_id:
            episode_data["tenant_id"] = self.tenant_id
        if self.project_id:
            episode_data["project_id"] = self.project_id

        response = await self.client.post("/episodes/", json=episode_data)
        response.raise_for_status()
        return response.json()

    async def generate_episodes(
        self, count: int, start_date: Optional[datetime] = None, random_dates: bool = False
    ) -> list:
        """
        Generate multiple episodes.

        Args:
            count: Number of episodes to generate
            start_date: Start date for episodes (defaults to now)
            random_dates: If True, randomize episode dates

        Returns:
            List of created episode responses
        """
        logger.info(f"Generating {count} episodes...")

        if start_date is None:
            start_date = datetime.now()

        episodes = []

        for i in range(count):
            content = self._generate_episode_content()

            # Generate a name for the episode
            name = f"Test Episode {i + 1}"

            # Create metadata
            metadata = {"test_data": True, "batch_id": str(uuid.uuid4()), "index": i}

            # Randomize date if requested
            valid_at = None
            if random_dates:
                days_offset = random.randint(-30, 0)
                hours_offset = random.randint(0, 23)
                valid_at = start_date + timedelta(days=days_offset, hours=hours_offset)

            try:
                episode = await self.create_episode(
                    content=content, name=name, metadata=metadata, valid_at=valid_at
                )
                episodes.append(episode)

                # Progress logging
                if (i + 1) % 10 == 0:
                    logger.info(f"Created {i + 1}/{count} episodes")

            except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.NetworkError) as e:
                logger.error(f"Failed to create episode {i + 1}: {type(e).__name__}: {e}")
                continue

        logger.info(f"Successfully created {len(episodes)}/{count} episodes")
        return episodes

    async def generate_user_activity_series(
        self, user_name: str, days: int = 7, episodes_per_day: int = 5
    ) -> list:
        """
        Generate a realistic series of episodes for a specific user.

        This creates a coherent activity pattern showing a user's
        interactions over time.

        Args:
            user_name: Name of the user
            days: Number of days of activity to generate
            episodes_per_day: Average episodes per day

        Returns:
            List of created episodes
        """
        logger.info(f"Generating activity series for {user_name} over {days} days")

        all_episodes = []
        current_date = datetime.now() - timedelta(days=days)

        for day in range(days):
            # Vary the number of episodes per day
            num_episodes = random.randint(max(1, episodes_per_day - 2), episodes_per_day + 2)

            for episode_num in range(num_episodes):
                # Create user-specific content
                content_templates = [
                    f"{user_name} {{action}} in the morning.",
                    f"Afternoon activity: {user_name} {{action}}.",
                    f"{user_name} completed {{action}} before lunch.",
                    f"Evening session: {user_name} worked on {{action}}.",
                    f"{user_name} documented their {{action}}.",
                ]

                actions = [
                    "analyzed data trends",
                    "reviewed project requirements",
                    "updated knowledge base",
                    "collaborated with team members",
                    "prepared reports",
                    "conducted research",
                    "attended virtual meetings",
                    "optimized workflows",
                    "documented findings",
                    "shared insights with the team",
                ]

                template = random.choice(content_templates)
                content = template.format(action=random.choice(actions))

                # Calculate specific time for this episode
                hour = random.randint(8, 18)  # Business hours
                minute = random.randint(0, 59)
                episode_time = current_date.replace(
                    hour=hour, minute=minute, second=random.randint(0, 59)
                )

                metadata = {
                    "test_data": True,
                    "user_series": user_name,
                    "day": day,
                    "episode_number": episode_num,
                }

                try:
                    episode = await self.create_episode(
                        content=content,
                        name=f"{user_name} - Day {day + 1} - Activity {episode_num + 1}",
                        metadata=metadata,
                        valid_at=episode_time,
                    )
                    all_episodes.append(episode)
                except httpx.HTTPStatusError as e:
                    logger.error(f"Failed to create episode: {e}")

            current_date += timedelta(days=1)

        logger.info(f"Generated {len(all_episodes)} episodes for {user_name}")
        return all_episodes

    async def generate_project_collaboration(
        self, project_name: str, team_members: list[str], days: int = 14
    ) -> list:
        """
        Generate realistic team collaboration episodes for a project.

        This simulates a team working together on a project with
        coordinated activities, discussions, and handoffs.

        Args:
            project_name: Name of the project
            team_members: List of team member names
            days: Number of days to simulate

        Returns:
            List of created episodes
        """
        logger.info(f"Generating collaboration data for project '{project_name}'")

        all_episodes = []
        current_date = datetime.now() - timedelta(days=days)

        collaboration_events = [
            "{member} kicked off the {project} initiative with initial planning.",
            "{member} conducted stakeholder interviews for {project}.",
            "Team meeting: {member} presented {project} requirements analysis.",
            "{member} created technical specifications for {project}.",
            "{member} reviewed {project} documentation and provided feedback.",
            "{member} implemented core features for {project}.",
            "Code review: {member} checked {project} implementation.",
            "{member} tested {project} functionality and reported results.",
            "{member} deployed {project} to staging environment.",
            "{member} documented {project} deployment procedures.",
            "{member} trained users on {project} features.",
            "{member} gathered user feedback for {project} improvements.",
            "Retrospective: {member} shared insights on {project} progress.",
            "{member} updated {project} roadmap based on team feedback.",
            "{member} archived {project} deliverables and documentation.",
        ]

        events_per_day = random.randint(2, 5)

        for day in range(days):
            # Shuffle team members for variety
            random.shuffle(team_members)

            for event_num in range(events_per_day):
                member = team_members[event_num % len(team_members)]
                event_template = random.choice(collaboration_events)
                content = event_template.format(member=member, project=project_name)

                # Realistic business hours timing
                hour = random.randint(9, 17)
                minute = random.choice([0, 15, 30, 45])
                episode_time = current_date.replace(
                    hour=hour, minute=minute, second=random.randint(0, 59)
                )

                metadata = {
                    "test_data": True,
                    "project_name": project_name,
                    "team_member": member,
                    "collaboration_type": "project_work",
                }

                try:
                    episode = await self.create_episode(
                        content=content,
                        name=f"{project_name} - Day {day + 1} - Event",
                        metadata=metadata,
                        valid_at=episode_time,
                    )
                    all_episodes.append(episode)
                except httpx.HTTPStatusError as e:
                    logger.error(f"Failed to create episode: {e}")

            current_date += timedelta(days=1)

        logger.info(f"Generated {len(all_episodes)} collaboration episodes")
        return all_episodes


async def get_default_api_key(base_url: str) -> Optional[str]:
    """
    Get the default development API key from the server.

    Args:
        base_url: API base URL

    Returns:
        Default API key if available, None otherwise
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Try to list API keys - the dev server usually has a default key
            response = await client.get(f"{base_url}/auth/keys")
            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, list) and len(data) > 0:
                    # Return the first (default) key
                    return data[0].get("key")
    except Exception as e:
        logger.warning(f"Could not fetch default API key: {e}")
    return None


async def main():
    """Main entry point for test data generation."""
    parser = argparse.ArgumentParser(description="Generate test data for MemStack")
    parser.add_argument("--api-url", default="http://localhost:8000/api/v1", help="API base URL")
    parser.add_argument(
        "--api-key", help="API key for authentication (will fetch default if not provided)"
    )
    parser.add_argument("--tenant-id", help="Tenant ID (will create new if not provided)")
    parser.add_argument("--project-id", help="Project ID (will create new if not provided)")
    parser.add_argument(
        "--count", type=int, default=50, help="Number of random episodes to generate"
    )
    parser.add_argument(
        "--mode",
        choices=["random", "user-series", "collaboration"],
        default="random",
        help="Generation mode",
    )
    parser.add_argument("--user-name", help="User name for user-series mode")
    parser.add_argument(
        "--project-name", default="Test Project", help="Project name for collaboration mode"
    )
    parser.add_argument(
        "--days", type=int, default=7, help="Number of days for user-series or collaboration mode"
    )

    args = parser.parse_args()

    # Get API key - from args, environment, or fetch default
    api_key = args.api_key
    if not api_key:
        # Try environment variable
        import os

        api_key = os.environ.get("API_KEY")
        if not api_key:
            # Try to fetch default from server
            logger.info("No API key provided, attempting to fetch default...")
            api_key = await get_default_api_key(args.api_url)
            if api_key:
                logger.info("Using default API key from server")
            else:
                logger.error(
                    "No API key provided. Please:\n"
                    "  1. Pass --api-key argument\n"
                    "  2. Set API_KEY environment variable\n"
                    "  3. Ensure server is running with default credentials"
                )
                return

    async with TestDataGenerator(
        base_url=args.api_url, api_key=api_key, tenant_id=args.tenant_id, project_id=args.project_id
    ) as generator:
        if args.mode == "random":
            # Generate random episodes
            episodes = await generator.generate_episodes(count=args.count, random_dates=True)
            logger.info(f"Generated {len(episodes)} random episodes")

        elif args.mode == "user-series":
            # Generate user activity series
            if not args.user_name:
                args.user_name = random.choice(TestDataGenerator.NAMES)

            episodes = await generator.generate_user_activity_series(
                user_name=args.user_name, days=args.days
            )
            logger.info(f"Generated {len(episodes)} user activity episodes")

        elif args.mode == "collaboration":
            # Generate project collaboration data
            team_members = random.sample(TestDataGenerator.NAMES, k=5)

            episodes = await generator.generate_project_collaboration(
                project_name=args.project_name, team_members=team_members, days=args.days
            )
            logger.info(f"Generated {len(episodes)} collaboration episodes")

    logger.info("Test data generation complete!")


if __name__ == "__main__":
    asyncio.run(main())
