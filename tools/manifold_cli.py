#!/usr/bin/env python3
import sys
import json
import tools.ledger_engine
import tordial_gs_manifold

def print_help():
    print("""
🌌 TORDIAL MANIFOLD CORE CLI SURFACE
Usage:
  python3 tools/manifold_cli.py [ledger_file] height
  python3 tools/manifold_cli.py [ledger_file] export [from_index]
  python3 tools/manifold_cli.py [ledger_file] import [json_payload_string]
  python3 tools/manifold_cli.py [ledger_file] enroll [actor_id] [weight] [ancestor_tag]
  python3 tools/manifold_cli.py [ledger_file] mint_cert [actor_id] [issuer] [lineage_root] [statement]
    """, file=sys.stderr)

def main():
    if len(sys.argv) < 3:
        print_help()
        sys.exit(1)

    ledger_path = sys.argv[1]
    command = sys.argv[2]

    print(f"🛠️  Initializing CLI target: {ledger_path}", file=sys.stderr)
    chain = tools.ledger_engine.LocalSovereignChain(ledger_file=ledger_path)
    
    if command == "height":
        print(chain.native_bridge.get_event_count())

    elif command == "export":
        if len(sys.argv) < 4:
            print("❌ Error: Missing target start index anchor.", file=sys.stderr)
            sys.exit(1)
        idx = int(sys.argv[3])
        payload = chain.native_bridge.export_portable_delta(idx)
        print(payload)

    elif command == "import":
        if len(sys.argv) < 4:
            print("❌ Error: Missing incoming JSON data string.", file=sys.stderr)
            sys.exit(1)
        raw_data = sys.argv[3]
        success = chain.native_bridge.import_portable_delta(raw_data)
        print(f"STATUS:{success}")

    elif command == "enroll":
        if len(sys.argv) < 6:
            print("❌ Error: Missing parameters. [actor_id] [weight] [ancestor_tag]", file=sys.stderr)
            sys.exit(1)
        act_id = int(sys.argv[3])
        wt = float(sys.argv[4])
        tag = sys.argv[5]
        chain.native_bridge.register_enrolment_node(act_id, wt, tag)

    elif command == "mint_cert":
        if len(sys.argv) < 7:
            print("❌ Error: Missing parameters. [actor_id] [issuer] [lineage_root] [statement]", file=sys.stderr)
            sys.exit(1)
        import time
        act_id = int(sys.argv[3])
        issuer = sys.argv[4]
        root = sys.argv[5]
        stmt = sys.argv[6]
        h = chain.native_bridge.publish_handshake_certificate(int(time.time()), act_id, issuer, root, stmt)
        print(f"COMMITTED_HASH:{h}")

    else:
        print_help()

if __name__ == "__main__":
    main()
