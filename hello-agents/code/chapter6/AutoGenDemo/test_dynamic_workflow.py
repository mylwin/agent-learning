"""不调用模型，验证动态回退与终止边界。"""
import unittest
from dynamic_workflow import parse_review, run_workflow


class ReviewParsingTests(unittest.TestCase):
    def test_fenced_and_plain_json(self):
        for text in ('{"verdict":"approve","feedback":"通过"}',
                     '```json\n{"verdict":"approve","feedback":"通过"}\n```',
                     '```\r\n{"verdict":"approve","feedback":"通过"}\r\n```'):
            with self.subTest(text=text):
                self.assertEqual(parse_review(text)['verdict'], 'approve')

    def test_reject_invalid_or_mixed_output(self):
        for text in ('说明\n```json\n{"verdict":"approve","feedback":"通过"}\n```',
                     '```json\n{"verdict":"code_change","feedback":""}\n```',
                     '```json\n{invalid}\n```'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_review(text)


class WorkflowTests(unittest.IsolatedAsyncioTestCase):
    async def test_fenced_review_routes_back_to_engineer(self):
        calls = []
        answers = iter(['需求', '代码1', '```json\n{"verdict":"code_change","feedback":"修复"}\n```',
                        '代码2', '{"verdict":"approve","feedback":"通过"}'])
        async def ask(role, prompt):
            calls.append((role, prompt))
            return next(answers)
        result = await run_workflow('任务', ask)
        self.assertEqual([role for role, _ in calls],
                         ['ProductManager', 'Engineer', 'CodeReviewer', 'Engineer', 'CodeReviewer'])
        self.assertIn('修复', calls[3][1])
        self.assertEqual(result.status, 'ready_for_acceptance')

    async def test_requirements_rollback_and_approval(self):
        calls = []
        answers = iter(['初始需求', '代码1', '{"verdict":"requirements_change","feedback":"修改需求"}',
                        '更新需求', '代码2', '{"verdict":"approve","feedback":"通过"}'])
        async def ask(role, prompt):
            calls.append((role, prompt))
            return next(answers)
        result = await run_workflow('任务', ask)
        self.assertEqual([role for role, _ in calls], ['ProductManager', 'Engineer', 'CodeReviewer',
                                                        'ProductManager', 'Engineer', 'CodeReviewer'])
        self.assertIn('代码1', calls[3][1])
        self.assertIn('更新需求', calls[4][1])
        self.assertEqual(result.status, 'ready_for_acceptance')
        self.assertEqual(result.code, '代码2')

    async def test_code_rollback_limit(self):
        calls = []
        async def ask(role, prompt):
            calls.append(role)
            return '{"verdict":"code_change","feedback":"修复错误"}' if role == 'CodeReviewer' else '内容'
        result = await run_workflow('任务', ask, max_rollbacks=1)
        self.assertEqual(calls, ['ProductManager', 'Engineer', 'CodeReviewer', 'Engineer', 'CodeReviewer'])
        self.assertEqual(result.status, 'needs_human_review')

    async def test_invalid_review_stops(self):
        async def ask(role, prompt):
            return '不是 JSON' if role == 'CodeReviewer' else '内容'
        result = await run_workflow('任务', ask)
        self.assertEqual(result.status, 'needs_human_review')
        self.assertEqual(result.history[-1]['verdict'], 'invalid_review')


if __name__ == '__main__':
    unittest.main()
