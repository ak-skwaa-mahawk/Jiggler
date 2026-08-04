# Add the project root to system paths dynamically to bind the components cleanly
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.policy_governance.evaluator import SovereignPolicyGuard
from core.octagonal_fpt_agent import OctagonalFPTAgent
