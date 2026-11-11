import unittest

from research.e495_time2_mixed_sign_oracle import run_campaign


class E495MixedSignOracleTests(unittest.TestCase):
    def test_frozen_campaign_preserves_direction_and_failure_atomicity(self):
        result = run_campaign(random_cases=512, seed=495)
        counts = result["counts"]
        self.assertEqual(result["total_cases"], 8 + 42 + 512)
        self.assertEqual(counts["accepted"] + counts["rejected"], result["total_cases"])
        self.assertEqual(counts["direction_failures"], 0)
        self.assertEqual(counts["output_mutations_on_reject"], 0)
        self.assertEqual(counts["exact_accepted"] + counts["inexact_accepted"], counts["accepted"])
        self.assertGreater(counts["canonical_two_component_witnesses"], 0)

    def test_structured_subulp_and_overflow_boundaries_are_present(self):
        result = run_campaign(random_cases=0, seed=495)
        cases = {row["case"]: row for row in result["boundary_cases"]}
        self.assertEqual(set(cases), {
            "positive_sub_low_resolution",
            "negative_sub_low_resolution",
            "exact_cancellation",
            "minimum_subnormal_addition",
            "minimum_subnormal_cancellation",
            "max_plus_min_subnormal",
            "max_minus_min_subnormal",
            "overflow_rejection",
        })
        self.assertFalse(cases["positive_sub_low_resolution"]["accepted"])
        self.assertFalse(cases["negative_sub_low_resolution"]["accepted"])
        self.assertTrue(cases["exact_cancellation"]["accepted"])
        self.assertTrue(cases["minimum_subnormal_addition"]["accepted"])
        self.assertFalse(cases["overflow_rejection"]["accepted"])
        self.assertTrue(cases["overflow_rejection"]["output_unchanged_on_reject"])


if __name__ == "__main__":
    unittest.main()
