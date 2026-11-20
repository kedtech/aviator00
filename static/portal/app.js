document.addEventListener("DOMContentLoaded", () => {
  // Quick amount buttons
  const amount = document.querySelector("#points");
  document.querySelectorAll("[data-value]").forEach((btn) =>
    btn.addEventListener("click", () => {
      if (amount) amount.value = btn.dataset.value;
    })
  );

  const form = document.querySelector("#numberForm");
  if (!form) return;

  const fields = [...form.querySelectorAll('input[name="numbers"]')];

  // Auto-advance to next box when a value is entered
  fields.forEach((input, i) => {
    // Only allow digits
    input.addEventListener("input", () => {
      input.value = input.value.replace(/\D/g, "");

      const maxLen = parseInt(input.getAttribute("maxlength") || "2", 10);
      if (input.value.length > maxLen) {
        input.value = input.value.slice(0, maxLen);
      }

      // Move to next when this box is "full"
      if (input.value.length >= maxLen && i < fields.length - 1) {
        fields[i + 1].focus();
        fields[i + 1].select();
      }
    });

    // Backspace on empty field → previous box
    input.addEventListener("keydown", (e) => {
      if (e.key === "Backspace" && !input.value && i > 0) {
        e.preventDefault();
        fields[i - 1].focus();
        fields[i - 1].select();
      }
      // Arrow keys
      if (e.key === "ArrowLeft" && i > 0) {
        fields[i - 1].focus();
      }
      if (e.key === "ArrowRight" && i < fields.length - 1) {
        fields[i + 1].focus();
      }
    });
  });

  // Submit validation: all filled + unique
  form.addEventListener("submit", (e) => {
    const vals = fields.map((x) => x.value.trim());
    if (vals.some((v) => v === "") || new Set(vals).size !== vals.length) {
      e.preventDefault();
      alert("Please enter a different valid number in every box.");
    }
  });
});
