# 💡 MV* Patterns in Python: MVC / MVP / MVVM

This project demonstrates three architectural UI patterns — **MVC**, **MVP**, and **MVVM** — using the same domain logic (a tiny “bank transfer” use case).  
All examples are in plain Python with a console UI.

The goal is to show:
- How each pattern structures responsibilities between UI and business logic,
- How data flows (who calls whom),
- How “ports” and dependency inversion keep the domain pure.

You’ll find these modules:

- `datatypes.py` – shared data structures and the `TransferPort` protocol.
- `domain.py` – the domain layer (`Bank`, `Treasury`, `Exchange`). No I/O.
- `mvc_app.py` – MVC version.
- `mvp_app.py` – MVP (Passive View) version.
- `mvvm_app.py` – MVVM version.

All three UIs perform the same scenario:
- Ask the user: from which account to transfer, to which account, what amount.
- If currencies differ, ask for confirmation of the conversion.
- Show progress for each step of the transfer.
- Perform the money movement.
- Show success or failure.

Everything is fully in-memory — no files, no DB, no network.

---

## 🧪 MVC

### Explanation

**Smalltalk MVC vs. Simplified MVC:**  
- Smalltalk/traditional MVC: the View owns user events; the Controller reacts to those events and never reads inputs directly.  
- Simplified MVC (common in CLI demos): the Controller often reads inputs directly.  

This version is closer to Smalltalk MVC: the Controller asks the View to gather input (`get_transfer_inputs`) and then orchestrates, while the Model remains UI-agnostic behind a port.

In this example, there is an additional class — **Controller** — that stands between the View and the Model.  
The Controller holds references to both the View and the Model.  
It asks the View for user input, calls the Model’s methods, and tells the View what to display.

The Controller passes itself to the Model as an interface (via the `TransferPort` protocol).  
This is **Dependency Inversion**: the Model doesn’t know about the concrete Controller (and doesn’t know about the View), but during a longer business operation it can call methods of this interface — for example, to report progress, request confirmation, or signal completion.  
The Controller implements this interface and simply delegates visualization to the View.

The View does not store a reference to the Controller and does not notify it about user actions on its own.  
Therefore, the interaction does not go automatically in the direction “User → View → Controller.”  
Instead, the Controller itself starts the scenario (`run`), requests input from the View, and controls the whole flow.

The original **Smalltalk-style MVC** worked slightly differently:
- The View held a reference to its Controller.  
- User events (mouse, keyboard) first reached the View, which immediately called the Controller.  
- The Controller then modified the Model.  
- The View *observed* the Model: the Model notified the View about changes via the Observer pattern, and the View redrew itself.

#### Component summary

Model: Bank orchestrates a multi-step transfer and is fully UI-agnostic. It communicates out via the TransferPort only; Treasury and Exchange are pure domain services.

View: ConsoleTransferView is responsible for collecting inputs and rendering (progress, confirmation prompt, result, errors). No business rules.

Controller: TransferController coordinates the flow. It asks the View for inputs (get_transfer_inputs()), validates/parses, invokes Bank.transfer(...), and implements TransferPort by delegating progress/confirmation/result to the View.

#### MVC diagram
```text
            +-----------------------+
            |        View           |
            |  ConsoleTransferView  |
            |  - get_transfer_inputs|
            |  - show_* / ask_*     |
            +-----------^-----------+
                        |
                        | implements TransferPort via Controller
                        |
            +-----------+-----------+
            |      Controller       |
            |   TransferController  |
            | - run()               |
            | - report_transfer_*   |
            | - confirm_currency_*  |
            | - discard_transfer()  |
            +-----------^-----------+
                        |
                        | calls
                        |
            +-----------+-----------+
            |         Model         |
            |   Bank (orchestrator) |
            |     /        \        |
            | Treasury     Exchange |
            +-----------------------+
```

---

## 🧪 MVP

### Explanation

In many real-world MVC implementations, the Controller can and often does talk to the UI directly. For example:  
- In web MVC (like Django or Rails), the Controller (view function/action) renders templates or returns HTTP responses directly — it owns the UI output.  
- In GUI frameworks (like early Smalltalk or Cocoa MVC), Controllers often manipulate UI widgets (show/hide, update labels) instead of delegating through a separate View interface.

In **MVP**, the **Presenter** never manipulates UI elements directly — it always goes through the View’s abstracted interface.  
The Presenter is UI-agnostic and fully unit-testable with a minimal fake View.

In this MVP example, just like in MVC, there is a layer between the View and the Model — but in MVP that layer is called **Presenter**, not Controller.  
The main difference is that in MVP, it is **the View** that initiates user events and calls the Presenter, not the Presenter that pulls input from the View.

The connection works like this:
- The View binds itself to the Presenter (the Presenter initiates this since it has a reference to the View).  
  The View stores a reference to the Presenter’s method (e.g. `on_submit`) and later calls it when the user enters data.  
  So the event originates in the View, but the logic for handling it lives in the Presenter.  
- The Presenter receives the raw data from the View and calls the business operation on the Model.  
- The Presenter implements the `TransferPort` interface, so that during execution the Model can report progress, ask for confirmation, or notify completion.  
  The Presenter simply delegates all such calls back to the View (to show progress, ask for confirmation, or display an error).

Thus:
- The View knows the Presenter only through the bound callback (`on_submit`) and contains no business logic — it’s responsible only for input/output.  
  In canonical MVC, the View observes the Model, but in MVP the View only reports user actions to the Presenter through a callback.  
- The Presenter knows both the View and the Model (similar to how the Controller does in MVC).  
- The Model, just like in the MVC version, knows neither View nor Presenter directly — it interacts only via the abstract `TransferPort` interface, which the Presenter implements.  
  This is Dependency Inversion in practice.

This implementation of MVP closely follows the **classic Passive View MVP pattern**, while the MVC version is a more modern layered variant that departs from the original Smalltalk-style MVC.

#### Component summary

View (Passive) gathers raw inputs once (run_once) and pushes them to the Presenter via the bound handler. It exposes only render commands (show_transfer_progress, show_transfer_result, show_transfer_error) and a prompt (ask_exchange_confirmation). No business logic lives here.

Presenter owns all presentation logic: it parses/validates the amount, calls the Model (Bank.transfer), and implements TransferPort so the domain can report progress, ask for confirmation, complete, or discard. Each port callback is translated into a simple View call.

Model (Bank orchestrating Treasury + Exchange) is UI-agnostic and communicates outward only through TransferPort.

#### MVP diagram
```text
                +------------------------+
                |          View          |
                |  ConsoleTransferView   |
                |  - bind_submit(h)      |
user input ---> |  - run_once()          | --render / prompt--> (prints, input)
                |  - show_transfer_*     |
                |  - ask_exchange_*()    |
                +-----------^------------+
                            |
                   pushes raw inputs
                            |
                +-----------+------------+
                |        Presenter        |
                |   TransferPresenter     |
                | - on_submit(...)        |
                | - implements            |
                |   TransferPort:         |
                |   report_* / confirm_*  |
                |   / discard_transfer    |
                +-----------^-------------+
                            |
                            | calls
                            |
                +-----------+-----------+
                |         Model         |
                |   Bank (orchestrator) |
                |     /        \        |
                | Treasury     Exchange |
                +-----------------------+
```

---

## 🧪 MVVM

### Explanation

Just like in MVC and MVP, MVVM also has a layer between the View and the Model.  
In MVVM, this layer is called the **ViewModel**.  
The View receives a reference to the ViewModel (which is somewhat similar to canonical MVC, where the View holds a reference to its Controller; in MVP, the View doesn’t store the whole Presenter — it only keeps callbacks bound to its methods).

As in MVP, during a user scenario the View collects user input or reacts to a user action (button press / form submit).  
But from that point, the behavior differs:

- In **MVP**, the View calls the Presenter through a bound method (for example, calls `on_submit`, which is actually implemented in the Presenter).  
- In **MVVM**, the View does **not** pass data as handler arguments. Instead, the View directly writes input values into the ViewModel (sets `vm.from_id`, `vm.to_id`, `vm.amount_text`, etc.), and then calls a command on the ViewModel (for example, `vm.run_transfer()`).

The key idea of MVVM here is that the ViewModel reads those values as its own **internal state** (input state).  
This is convenient when input is collected from several UI fields or at different times — the ViewModel doesn’t receive the whole “form” as a single call parameter (as the Presenter typically does), but maintains a **live state** that the View simply binds to.

Another important difference is that the ViewModel never calls the View’s methods directly.  
Instead, the ViewModel exposes **signals / callbacks** (for example, `on_progress`, `on_error`, `on_result`, `on_confirm_request`).  
The View subscribes to these callbacks and assigns its own methods (such as `show_transfer_progress`, `show_transfer_error`, etc.).  
So when the domain logic — via the ViewModel — reports something like “progress step 2 of 4,” the ViewModel does not call the View directly, but simply triggers a callback that the View has already bound.

To compare:
- In **MVP**, the Presenter simply knows the View object and calls methods like `view.show_transfer_progress(...)` directly.  
- In **MVVM**, the ViewModel has no reference to the View at all. It only calls its own callbacks (signals), and those callbacks happen to point to the View’s methods.

The way the ViewModel communicates with the Model is the same as in MVP — through **Dependency Inversion** (our `TransferPort` interface, which the ViewModel implements).  
Just like in MVP (and in our MVC variant too), the View contains no business logic and only handles input/output, while the Model knows nothing about the View, Presenter, or ViewModel and interacts with the outside world only through the abstract interface.

#### Component summary

View: ConsoleTransferView holds a reference to the ViewModel. It gathers user input (from_id, to_id, amount_text), writes it into the ViewModel, binds ViewModel callbacks to its own rendering methods, and finally calls vm.run_transfer(). The View contains no business rules — only I/O and binding logic.

ViewModel: TransferViewModel holds all UI-related state (input/output). It exposes binding hooks (bind_on_progress, bind_on_error, bind_on_result, bind_confirm_callback) for the View to connect its methods. It validates inputs, calls the Model (Bank.transfer), and implements TransferPort so the domain can send progress updates, confirmation requests, or completion messages. The ViewModel doesn’t know about the View — only its callbacks.

Model: Bank, Treasury, and Exchange form the pure domain layer. Bank orchestrates the process, calls back into the TransferPort (here, the ViewModel), and remains unaware of the View or ViewModel.

#### MVVM diagram
```text
              ┌──────────────────────────────────────────────┐
              │                   User                       │
              │    (inputs: from_id, to_id, amount_text)     │
              └──────────────────────────────────────────────┘
                                      │
                                      ▼
                     ┌─────────────────────────────────┐
                     │             View                │
                     │      ConsoleTransferView        │
                     │─────────────────────────────────│
                     │ - gathers input via input()     │
                     │ - sets vm.from_id, vm.to_id,    │
                     │   vm.amount_text                │
                     │ - binds VM callbacks            │
                     │ - displays UI output            │
                     └─────────────────────────────────┘
                                      │
                           (writes input state)
                                      │
                                      ▼
                     ┌─────────────────────────────────┐
                     │           ViewModel             │
                     │       TransferViewModel         │
                     │─────────────────────────────────│
                     │ - holds input/output state      │
                     │ - exposes bind_*() methods      │
                     │ - calls Bank.transfer()         │
                     │ - implements TransferPort       │
                     │ - triggers callbacks to View    │
                     └─────────────────────────────────┘
                                      │
                           (dependency injection)
                                      │
                                      ▼
                     ┌───────────────────────────────────────────────┐
                     │             Model                             │
                     │  Bank + Treasury + Exchange                   │
                     │───────────────────────────────────────────────│
                     │ - pure business logic                         │
                     │ - no UI code                                  │
                     │ - calls ViewModel via TransferPort interface  │
                     └───────────────────────────────────────────────┘
                                      │
                                      ▼
                     ┌────────────────────────────────────────┐
                     │         CALLBACK FLOW                  │
                     │ (Bank → ViewModel → View)              │
                     │ e.g. report_progress() → on_progress() │
                     └────────────────────────────────────────┘
```

---

## ⚙️ Sample Execution

All three implementations behave the same from the user’s perspective:

```bash
% uv run mvc_app.py
From account: alice
To account: bob
Amount: 10
Progress: [1/4]
Progress: [2/4]
Convert 10.00 USD -> 9.00 EUR at 0.9000
Proceed? [y/N]: y
Progress: [3/4]
Progress: [4/4]
DONE: Transfer completed
```
```
% uv run mvp_app.py
From account: alice
To account: bob
Amount: 10
Progress: [1/4]
Progress: [2/4]
Convert 10.00 USD -> 9.00 EUR at 0.9000
Proceed? [y/N]: y
Progress: [3/4]
Progress: [4/4]
DONE: Transfer completed
```
```
% uv run mvvm_app.py
From account: alice
To account: bob
Amount: 10
Progress: [1/4]
Progress: [2/4]
Convert 10.00 USD -> 9.00 EUR at 0.9000
Proceed? [y/N]: y
Progress: [3/4]
Progress: [4/4]
DONE: Transfer completed
```

---

## 🚀 Final thoughts

- The domain (`Bank`, `Treasury`, `Exchange`) is completely UI-agnostic.
- It reports progress, asks for confirmation, and signals completion using the `TransferPort` interface.
- In MVC, the `Controller` implements that port.  
- In MVP, the `Presenter` implements that port.  
- In MVVM, the `ViewModel` implements that port.

That reuse is the point: you can swap UI patterns without changing the business logic.  
This is a practical illustration of Dependency Inversion and ports/adapters layered onto classic UI architectures.
