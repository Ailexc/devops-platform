package api

import "testing"

func TestBuildConditionCEL(t *testing.T) {
	cases := []struct {
		field, op, value string
		values           []string
		want             string
	}{
		{"env", "==", "prod", nil, `env == "prod"`},
		{"env", "!=", "dev", nil, `env != "dev"`},
		{"tags", "contains", "web", nil, `tags.contains("web")`},
		{"name", "startsWith", "web", nil, `name.startsWith("web")`},
		{"account_id", "in", "", []string{"a", "b"}, `account_id in ["a", "b"]`},
		{"account_id", "!in", "", []string{"a"}, `!(account_id in ["a"])`},
		{"owner_id", "==", "@currentUser", nil, `owner_id == "@currentUser"`},
	}
	for _, c := range cases {
		got, err := buildConditionCEL(c.field, c.op, c.value, c.values)
		if err != nil {
			t.Fatalf("%s %s: %v", c.field, c.op, err)
		}
		if got != c.want {
			t.Fatalf("got %q want %q", got, c.want)
		}
	}
}

func TestValidateCEL(t *testing.T) {
	valid := []string{
		`env == "prod"`,
		`tags.contains("web")`,
		`name.startsWith("web")`,
		`account_id in ["a", "b"]`,
		`!(account_id in ["a"])`,
		`owner_id == "@currentUser"`,
	}
	for _, e := range valid {
		if err := validateCEL(e); err != nil {
			t.Fatalf("valid %q rejected: %v", e, err)
		}
	}
	if err := validateCEL(`env == `); err == nil {
		t.Fatal("invalid CEL accepted")
	}
}
