> You can download the code of this step [here](../src/step_02.py) or all the steps [here](https://github.com/Avaiga/taipy-getting-started-core/tree/develop/src).

# Basic functions

*Time to complete: 15 minutes; Level: Beginner*

Let's discuss some of the essential functions that come along with Taipy.

- [`<Data Node>.write(<new value>)`](https://docs.taipy.io/en/latest/manuals/core/entities/data-node-mgt/#read-write-a-data-node): this instruction changes the data of a Data Node.

- [`tp.get_scenarios()`](https://docs.taipy.io/en/latest/manuals/core/entities/scenario-cycle-mgt/#get-all-scenarios): this function returns the list of all the scenarios.

- [`tp.get(<Taipy object ID>)`](https://docs.taipy.io/en/latest/manuals/core/entities/data-node-mgt/#get-data-node): this function returns an entity based on the id of the entity.

- [`tp.delete(<Taipy object ID>)`](https://docs.taipy.io/en/latest/manuals/core/entities/scenario-cycle-mgt/#delete-a-scenario): this function deletes the entity and nested elements based on the id of the entity.

## Utility of having scenarios

Taipy lets the user create multiple instances of the same configuration. Data can differ between different scenario instances. It is essential to understand the difference in data between scenario instances. Such differences in scenarios can be due to the following:

- Changing data from input data nodes, 

- Randomness in a task (random algorithm), 

- Different values from parameters set by the end-user, etc.

The developer can directly change the data nodes entities with the _write_ function (see below).

![](config_02.svg){ width=700 style="margin:auto;display:block;border: 4px solid rgb(210,210,210);border-radius:7px" }

```python
scenario = tp.create_scenario(scenario_cfg, name="Scenario")
tp.submit(scenario)
print("Output of First submit:", scenario.output.read())
```

Results:

```
[2022-12-22 16:20:02,874][Taipy][INFO] job JOB_double_a5ecfa4d-1963-4776-8f68-0859d22970b9 is completed.
Output of First submit: 42
```

## _write_ function

Data of a Data Node can be changed using _write_. The syntax is `<Scenario>.<Data Node>.write(value)`.


```python
print("Before write", scenario.input.read())
scenario.input.write(54)
print("After write",scenario.input.read())
```

Results:
```
Before write 21
After write 54
```

The submission of the scenario updates the output values.


```python
tp.submit(scenario)
print("Second submit",scenario.output.read())
```

Results:
```
[2022-12-22 16:20:03,011][Taipy][INFO] job JOB_double_7eee213f-062c-4d67-b0f8-4b54c04e45e7 is completed.
Second submit 108
```
    
## Other useful functions

- `tp.get_scenarios` accesses all the scenarios by returning a list.

```python
print([s.name for s in tp.get_scenarios()])
```

Results:
```
["Scenario"]
```

- Get an entity from its id:

```python
scenario = tp.get(scenario.id)
```

- Delete an entity through its id. For example, to delete a scenario:

```python
tp.delete(scenario.id)
```

## Ways of executing the code: Versioning

Taipy provides a [versioning system](https://docs.taipy.io/en/latest/manuals/core/versioning/) to keep track of the changes that a configuration experiences over time: new data sources, new parameters, new versions of your Machine Learning engine, etc. `python main.py -h` opens a helper to understand the versioning options at your disposal.

# Entire code

```python
from taipy import Config
import taipy as tp


def double(nb):
    return nb * 2

# Configuration in Python
input_data_node_cfg = Config.configure_data_node("input", default_data=21)
output_data_node_cfg = Config.configure_data_node("output")

task_cfg = Config.configure_task("double",
                                 double,
                                 input_data_node_cfg,
                                 output_data_node_cfg)

scenario_cfg = Config.configure_scenario(id="my_scenario",
                                                    task_configs=[task_cfg])


if __name__ == '__main__':
    tp.Core().run()

    scenario = tp.create_scenario(scenario_cfg, name="Scenario")
    tp.submit(scenario)
    print("Output of First submit:", scenario.output.read())

    print("Before write", scenario.input.read())
    scenario.input.write(54)
    print("After write",scenario.input.read())


    tp.submit(scenario)
    print("Second submit",scenario.output.read())

    # Basic functions of Taipy Core 
    print([s.name for s in tp.get_scenarios()])
    scenario = tp.get(scenario.id)
    tp.delete(scenario.id)

    scenario = None
    data_node = None

    tp.Gui("""<|{scenario}|scenario_selector|>
              <|{scenario}|scenario|>
              <|{scenario}|scenario_dag|>
              <|{data_node}|data_node_selector|>""").run()
```


