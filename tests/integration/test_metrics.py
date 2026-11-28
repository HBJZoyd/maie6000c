"""Keep operational metric cardinality bounded as saved questions accumulate."""


def test_metrics_use_route_templates_instead_of_question_ids(client):
    questions = [client.post("/questions", json={"question": f"手册测试问题 {i}"}).json()
                 for i in range(3)]
    for question in questions:
        assert client.get(f"/questions/{question['id']}").status_code == 200
    client.get("/not-a-valid-route-123")
    metrics = client.get("/metrics").text
    assert 'path="/questions/{question_id}"' in metrics
    assert 'path="unmatched"' in metrics
    assert all(question["id"] not in metrics for question in questions)
    assert "/not-a-valid-route-123" not in metrics
