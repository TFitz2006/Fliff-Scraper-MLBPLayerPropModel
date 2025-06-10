import json
from Algo.Mudolu.PredictStatModule import predict_stat

def rank_fliff_props(json_path, output_path="ranked_props_output.json"):
    with open(json_path, "r") as f:
        props_data = json.load(f)

    matchup = props_data.get("matchup", "")
    if "vs" not in matchup:
        print(" Invalid matchup format.")
        return

    team_a, team_b = [team.strip().split()[-1] for team in matchup.split("vs")]
    game_teams = [team_a, team_b]
    opponent_team = team_b  # You can improve this logic later

    results = []

    for player, props in props_data.items():
        if player == "matchup":
            continue

        for category, lines in props.items():
            try:
                predicted = predict_stat(
                    player_name=player,
                    prop_category=category.lower(),
                    opponent_team_name=opponent_team,
                    game_teams=game_teams
                )

                if predicted is None:
                    continue

                prop_line = float(lines["over"][0])
                over_odds = lines["over"][1]
                under_odds = lines["under"][1]

                favorability = predicted - prop_line

                results.append({
                    "player": player,
                    "category": category,
                    "line": prop_line,
                    "predicted": round(predicted, 2),
                    "favorability": round(favorability, 2),
                    "over_odds": over_odds,
                    "under_odds": under_odds
                })

            except Exception as e:
                print(f"⚠️ Error processing {player} - {category}: {e}")

    results.sort(key=lambda x: x["favorability"], reverse=True)

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f" Ranked props saved to: {output_path}")





rank_fliff_props("mlb_props_output.json", output_path="top_ranked_props.json")
