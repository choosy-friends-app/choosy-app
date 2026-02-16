document.addEventListener("DOMContentLoaded", () => {
  const voteButtons = document.querySelectorAll("[data-vote-button]")

  voteButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const baseVotes = Number(button.dataset.baseVotes || "0")
      const planId = button.dataset.planId || ""
      const activeClass = "is-voted"
      const icon = button.querySelector("span")

      if (button.classList.contains(activeClass)) {
        button.classList.remove(activeClass)
        button.textContent = `Vote (${baseVotes})`
      } else {
        button.classList.add(activeClass)
        button.textContent = `Voted (${baseVotes + 1})`
      }

      if (icon) {
        button.prepend(icon)
      }

      button.setAttribute("aria-pressed", String(button.classList.contains(activeClass)))
      button.dataset.planId = planId
    })
  })
})
