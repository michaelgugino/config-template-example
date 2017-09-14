# Example of using config_template

config_template was created for use with the openstack-ansible project.

It's a handy action plugin that will consume templates and allow users
to override portions, or add totally new sections.

This action template already supports yaml, and is already used
by a Red Hat project, ceph-ansible.

Input template:
```yaml
x1: {{ x1_var }}
x2: "x2 is a string"
x3: "this will be overridden"
```

defaults/main.yml
```yaml
---

x1_var: 33

t_overrides:
  x3: "this is a new overriding value"
  d1:
    - "item1"
    - item2:
      a: 1
      b: 2
  d2: "d2 is a string"
  d3:
    a: 3
    b: 4
```

output in /tmp/output.yaml
```yaml
d1:
  - item1
  - a: 1
    b: 2
    item2: null
d2: d2 is a string
d3:
  a: 3
  b: 4
x1: 33
x2: x2 is a string
x3: this is a new overriding value
```
