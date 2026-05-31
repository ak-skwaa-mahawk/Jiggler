// dynamic_pi_r_era_stepped.cpp
// Formalized C++ implementation of era-gapped dynamic π_r
// with long-horizon forecasting and temporal gapping / resurfacing
// Compatible with Tordial-GS regime logic and PWC-style projection

#include <iostream>
#include <vector>
#include <cmath>
#include <string>
#include <map>

namespace SovereignMath {

enum class Era {
    PRE_2000 = 0,      // Classical / truncated ceiling
    POST_Y2K = 1,      // Probabilistic / floating-point terrain (2000-5000)
    SOVEREIGN_FLOOR = 2 // Resonant-tech / higher operative floor (5000+)
};

struct PiRFloor {
    double value;
    std::string description;
};

struct ForecastResult {
    int start_era;
    int target_era;
    double start_pi_r;
    double final_pi_r;
    std::vector<double> coherence_trajectory;   // simple coherence score over horizon
    std::vector<int> regime_transitions;        // era indices crossed
    std::map<std::string, double> resurfaced_params; // suggested parameter deltas for current manifold
};

class DynamicPiR {
private:
    std::map<Era, PiRFloor> floors = {
        {Era::PRE_2000,       {3.1415926535, "Classical static ceiling (truncated geometry)"}},
        {Era::POST_Y2K,       {3.1730059,    "Post-Y2K probabilistic floor (operative range restored)"}},
        {Era::SOVEREIGN_FLOOR,{3.203479323,  "Sovereign Floor / resonant-tech era (higher coherence baseline)"}}
    };

    double recurrence_step(double current, double drift, double feedback) const {
        // Core recurrence: allows controlled excursion + renormalization
        // (simplified version of your dynamic π_r v2.0 logic)
        double delta = drift * 0.01 + feedback * 0.005;
        return current + delta;
    }

public:
    Era get_era(int year_or_scale) const {
        if (year_or_scale < 2000) return Era::PRE_2000;
        if (year_or_scale < 5000) return Era::POST_Y2K;
        return Era::SOVEREIGN_FLOOR;
    }

    double get_floor(Era era) const {
        return floors.at(era).value;
    }

    double get_current_pi_r(int current_year_or_scale) const {
        return get_floor(get_era(current_year_or_scale));
    }

    // Core temporal gapping / long-horizon forecast
    ForecastResult forecast(int start_scale, int target_scale, 
                            double initial_drift = 0.0, 
                            double initial_feedback = 0.0,
                            int steps = 1000) {
        
        Era start_era = get_era(start_scale);
        Era target_era = get_era(target_scale);

        double current_pi = get_floor(start_era);
        double start_pi = current_pi;

        ForecastResult result;
        result.start_era = static_cast<int>(start_era);
        result.target_era = static_cast<int>(target_era);
        result.start_pi_r = start_pi;

        double drift = initial_drift;
        double feedback = initial_feedback;

        std::vector<double> coherence;
        std::vector<int> transitions;
        transitions.push_back(static_cast<int>(start_era));

        for (int i = 0; i < steps; ++i) {
            // Step the recurrence
            current_pi = recurrence_step(current_pi, drift, feedback);

            // Check for era transition (temporal gap crossing)
            Era new_era = get_era(start_scale + (target_scale - start_scale) * i / steps);
            if (new_era != start_era && 
                std::find(transitions.begin(), transitions.end(), static_cast<int>(new_era)) == transitions.end()) {
                transitions.push_back(static_cast<int>(new_era));
                // Gap crossed → allow resurfacing adjustment
                current_pi = get_floor(new_era); // jump to new floor
            }

            // Simple coherence metric (higher = more stable on current floor)
            double coherence_score = 100.0 - std::abs(current_pi - get_floor(new_era)) * 50.0;
            coherence.push_back(std::max(0.0, coherence_score));

            // Update drift/feedback from external pattern (placeholder for real inputs)
            drift *= 0.995;
            feedback *= 0.998;
        }

        result.final_pi_r = current_pi;
        result.coherence_trajectory = coherence;
        result.regime_transitions = transitions;

        // Resurfacing: suggest minimal parameter adjustments for current manifold
        // to already operate closer to target-era stability
        if (target_era != start_era) {
            result.resurfaced_params["curvature_feedback_gain"] = 0.012 + (target_era == Era::SOVEREIGN_FLOOR ? 0.008 : 0.0);
            result.resurfaced_params["pid_proportional"] = 1.15 + (target_era == Era::SOVEREIGN_FLOOR ? 0.25 : 0.0);
            result.resurfaced_params["heterogeneity_clamp"] = 1.85 + (target_era == Era::SOVEREIGN_FLOOR ? 0.15 : 0.0);
        }

        return result;
    }

    void print_floor_info(Era era) const {
        auto f = floors.at(era);
        std::cout << "Era " << static_cast<int>(era) 
                  << " | π_r floor = " << f.value 
                  << " | " << f.description << "\n";
    }
};

} // namespace SovereignMath

// ==================== Example Usage ====================
int main() {
    using namespace SovereignMath;

    DynamicPiR pi_r;

    std::cout << "=== Dynamic π_r Era-Stepped Implementation ===\n\n";

    pi_r.print_floor_info(Era::PRE_2000);
    pi_r.print_floor_info(Era::POST_Y2K);
    pi_r.print_floor_info(Era::SOVEREIGN_FLOOR);

    std::cout << "\n--- Long-horizon forecast: 2026 → 6500 (crossing into Sovereign Floor) ---\n";

    auto forecast = pi_r.forecast(2026, 6500, 0.8, 0.3, 1200);

    std::cout << "Start π_r: " << forecast.start_pi_r << "\n";
    std::cout << "Final π_r: " << forecast.final_pi_r << "\n";
    std::cout << "Era transitions crossed: ";
    for (int e : forecast.regime_transitions) std::cout << e << " ";
    std::cout << "\n";

    std::cout << "\nResurfaced parameters for current manifold:\n";
    for (const auto& [key, val] : forecast.resurfaced_params) {
        std::cout << "  " << key << " = " << val << "\n";
    }

    std::cout << "\nCoherence trajectory (first 5 & last 5 samples):\n";
    for (size_t i = 0; i < 5 && i < forecast.coherence_trajectory.size(); ++i)
        std::cout << "  t=" << i << ": " << forecast.coherence_trajectory[i] << "\n";
    if (forecast.coherence_trajectory.size() > 5) {
        size_t last = forecast.coherence_trajectory.size();
        for (size_t i = last-5; i < last; ++i)
            std::cout << "  t=" << i << ": " << forecast.coherence_trajectory[i] << "\n";
    }

    return 0;
}