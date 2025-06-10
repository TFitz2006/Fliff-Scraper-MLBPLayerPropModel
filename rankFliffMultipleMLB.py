import json
from Algo.Mudolu.PredictStatModule import predict_stat  # Ensure PredictStatModule.py is in the same directory

def rank_fliff_props_from_multi_game_json(input_json_path, output_json_path, season="2025"):
    with open(input_json_path, "r") as f:
        data = json.load(f)

    all_ranked_props = []

    for game in data.get("games", []):
        matchup = game["matchup"]
        game_teams = [team.strip().split()[-1] for team in matchup.split(" vs ")]  # e.g., "BOS Red Sox" → "Red Sox"

        for player_name, props in game["props"].items():
            for category, lines in props.items():
                try:
                    line_value = float(lines["over"][0])
                except (TypeError, ValueError, IndexError):
                    continue

                try:
                    predicted = predict_stat(
                        player_name=player_name,
                        prop_category=category.lower(),
                        opponent_team_name=game_teams[1] if game_teams[0] in player_name else game_teams[0],
                        game_teams=game_teams,
                        season=season
                    )
                except Exception as e:
                    print(f"⚠️ Prediction error for {player_name} {category}: {e}")
                    continue

                if predicted is None:
                    continue

                favorability = predicted - line_value

                all_ranked_props.append({
                    "player": player_name,
                    "category": category,
                    "matchup": matchup,
                    "line": line_value,
                    "predicted": round(predicted, 2),
                    "favorability": round(favorability, 2),
                    "over_odds": lines["over"][1],
                    "under_odds": lines["under"][1]
                })

    all_ranked_props.sort(key=lambda x: x["favorability"], reverse=True)

    with open(output_json_path, "w") as f:
        json.dump(all_ranked_props, f, indent=2)

    print(f" Ranked props saved to {output_json_path}")

# Run it if this script is executed directly
if __name__ == "__main__":
    rank_fliff_props_from_multi_game_json("mlb_props_output.json", "top_ranked_props.json")