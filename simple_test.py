import sys
sys.stdout.reconfigure(encoding='utf-8')

print("Testing itinerary service...")
from services.itinerary_service import generate_itinerary

itinerary = generate_itinerary("杭州", 3, ["sightseeing", "food"], "medium")
print(f"City: {itinerary['city']}")
print(f"Days: {itinerary['days']}")
print(f"Day 1: {itinerary['days_plan'][0]['date']}")
print(f"  Morning: {itinerary['days_plan'][0]['morning']['place']}")
print("Success!")
