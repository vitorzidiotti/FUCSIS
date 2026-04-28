/**
 * Exibe uma notificação pop-up (toast) na tela.
 * @param {string} message - A mensagem a ser exibida.
 * @param {string} category - A categoria da mensagem ('sucesso', 'erro', 'info').
 */
function showToast(message, category = 'info') {
    // Pega o container onde os toasts serão inseridos
    const container = document.getElementById('toast-container');
    if (!container) return;

    // Cria o elemento do toast
    const toast = document.createElement('div');
    toast.className = `toast toast-${category}`; // Ex: toast toast-sucesso
    toast.textContent = message;

    // Adiciona o toast ao container
    container.appendChild(toast);

    // Define um tempo para o toast desaparecer
    setTimeout(() => {
        toast.classList.add('hide');
        // Remove o elemento do DOM após a animação de saída
        toast.addEventListener('animationend', () => {
            toast.remove();
        });
    }, 5000); // O pop-up some após 5 segundos
}

function updateFileName(input) {
    const fileName = input.files[0] ? input.files[0].name : "Escolher novo PDF";
    const display = document.getElementById('file-name-display');
    display.innerText = fileName;
    
    // Opcional: muda a cor da borda quando seleciona
    if (input.files[0]) {
        display.parentElement.style.borderColor = "#228be6";
        display.parentElement.style.background = "#e7f5ff";
    }
}