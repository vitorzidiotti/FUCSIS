{% extends "base.html" %}

{% block title %}Controle de Estoque{% endblock %}

{% block content %}
    <h1>Controle de Estoque</h1>

    {# --- Formulário Principal (POST para adicionar movimento) --- #}
    <form id="form-movimento" action="{{ url_for('estoque.adicionar_movimento') }}" method="POST">

        {# --- Sub-Formulário de Busca (GET para recarregar a página com resultados) --- #}
        <div class="form-container" style="background: #eee; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem;">
            <h2>Buscar Produto</h2>
            {# Este form envia para a MESMA rota ('estoque.estoque_mov') via GET #}
            <form method="GET" action="{{ url_for('estoque.estoque_mov') }}" style="display: flex; gap: 1rem; align-items: flex-end;">
                 {# Mantém a página atual na URL ao buscar #}
                 <input type="hidden" name="page" value="{{ page }}">
                 <div style="flex-grow: 1;">
                     <label for="produto_busca">Nome do Produto:</label>
                     {# O 'name' agora é 'produto_q' para a rota pegar #}
                     <input type="text" id="produto_busca" name="produto_q" placeholder="Digite para buscar..." value="{{ termo_busca_produto or '' }}" autocomplete="off">
                 </div>
                 <button type="submit" class="btn btn-blue">Buscar Produto</button>
            </form>

            {# --- Exibição dos Resultados da Busca --- #}
            {% if termo_busca_produto and produtos_encontrados is not none %} {# Mostra só se buscou algo #}
                <div style="margin-top: 1rem; border-top: 1px solid #ccc; padding-top: 1rem;">
                    <h4>Resultados da Busca por "{{ termo_busca_produto }}":</h4>
                    {% if produtos_encontrados %}
                        <p>Selecione o produto desejado:</p>
                        <ul style="list-style: none; padding: 0;">
                            {% for produto in produtos_encontrados %}
                                <li style="margin-bottom: 0.5rem; padding: 5px; border-bottom: 1px dotted #eee;">
                                    <input type="radio" name="id_produto" value="{{ produto.id_produto }}" id="prod_{{ produto.id_produto }}" required>
                                    <label for="prod_{{ produto.id_produto }}">
                                        <strong>{{ produto.nome }}</strong> (Estoque: {{ produto.estoque }})
                                    </label>
                                </li>
                            {% endfor %}
                        </ul>
                    {% else %}
                        <p style="color: grey;">Nenhum produto encontrado.</p>
                    {% endif %}
                </div>
            {% endif %}
            {# --- Fim dos Resultados da Busca --- #}
        </div>

        {# --- Campos Restantes do Formulário Principal --- #}
        <div class="form-container" style="background: #fff; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 8px rgba(0,0,0,0.05); margin-bottom: 2rem;">
            <h2>Detalhes da Movimentação</h2>
             <p style="color: #6c757d; font-size: 0.9em; margin-top: -1rem; margin-bottom: 1rem;">
                 Selecione o produto na busca acima antes de preencher os detalhes.
             </p>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; align-items: end;">
                <div>
                    <label for="tipo_mov">Tipo de Movimento:</label>
                    <select id="tipo_mov" name="tipo_mov" required>
                        <option value="ENTRADA">Entrada</option>
                        <option value="SAIDA">Saída</option>
                    </select>
                </div>

                <div>
                    <label for="quantidade">Quantidade:</label>
                    <input type="number" id="quantidade" name="quantidade" min="1" required>
                </div>

                <div style="grid-column: 1 / -1;">
                    <label for="motivo">Motivo/Observação:</label>
                    <input type="text" id="motivo" name="motivo" placeholder="Ex: Compra NF 123, Ajuste, Venda ID 45" required>
                </div>

                <button type="submit" class="btn btn-green" style="grid-column: 1 / -1;">Registrar Movimento</button>
            </div>
        </div>
    </form> {# --- Fim do Formulário Principal --- #}


    {# --- Tabela de Histórico (sem alterações aqui, exceto o colspan) --- #}
    <div class="table-container">
        <h2>Histórico de Movimentações (Últimas {{ per_page }} por página)</h2>
        <table>
            <thead>
                <tr>
                    <th>Produto</th>
                    <th>Tipo</th>
                    <th>Quantidade</th>
                    <th>Motivo</th>
                    <th>Data</th>
                </tr>
            </thead>
            <tbody>
                {% if movimentos %}
                    {% for mov in movimentos %}
                    <tr>
                        <td data-label="Produto">{{ mov.tb_produto.nome if mov.tb_produto and 'nome' in mov.tb_produto else 'Produto não encontrado' }}</td>
                        <td data-label="Tipo"><span style="font-weight: bold; color: {{ '#28a745' if mov.tipo_mov == 'ENTRADA' else '#dc3545' }};">{{ mov.tipo_mov }}</span></td>
                        <td data-label="Quantidade">{{ mov.quantidade }}</td>
                        <td data-label="Motivo">{{ mov.motivo }}</td>
                        <td data-label="Data">{{ mov.criado_em | format_br_datetime if mov.criado_em else '-'}}</td>
                    </tr>
                    {% endfor %}
                {% else %}
                    <tr>
                        <td colspan="5" class="no-results">Nenhuma movimentação de estoque registrada.</td>
                    </tr>
                {% endif %}
            </tbody>
        </table>

        {# --- Paginação (sem alterações) --- #}
        {% if total_pages > 1 %}
        <div class="pagination" style="margin-top: 1.5rem; text-align: center;">
             {% if page > 1 %} <a href="{{ url_for('estoque.estoque_mov', page=page-1, produto_q=termo_busca_produto) }}" class="btn btn-blue" style="margin-right: 0.5rem;">&laquo; Anterior</a> {% else %} <span class="btn btn-blue" style="margin-right: 0.5rem; opacity: 0.5; cursor: default;">&laquo; Anterior</span> {% endif %}
             <span style="margin: 0 1rem; font-weight: bold;">Página {{ page }} de {{ total_pages }}</span>
             {% if page < total_pages %} <a href="{{ url_for('estoque.estoque_mov', page=page+1, produto_q=termo_busca_produto) }}" class="btn btn-blue" style="margin-left: 0.5rem;">Próximo &raquo;</a> {% else %} <span class="btn btn-blue" style="margin-left: 0.5rem; opacity: 0.5; cursor: default;">Próximo &raquo;</span> {% endif %}
        </div>
        {% endif %}

    </div>
{% endblock %}

{% block scripts %}
{# REMOVIDO o script de autocomplete e de formatação de data #}
{% endblock %}