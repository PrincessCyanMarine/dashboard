# Dashboard

A simple dashboard for linux systems made in python (for a college project)

# Relatorio

O programa abre na guia do task manager.

Na parte debaixo da interface, há uma seleção de guias

## Task manager

### CPU, memória, swap
No topo estão informações sobre o uso de cpu, memória e swap; como porcentagem, uma barra, e no caso da memória e do swap, numeros

### processos
Logo abaixo estão as informações sobre processos. Os processos podem ser organizados por uso de CPU, uso de Memória ou PID

Um processo pode ser finalizado selecionando-o com o botão do meio do mouse

Precionar a tecla K, finaliza o processo selecionado

## File manager
Diretórios são cinza claros e arquivos cinza escuro

O botão esquerdo do mouse pode ser usado para acessar diretórios ou abrir arquivos.

O botão direito é usado para selecionar arquivos. Arquivos selecionados aparecem em uma cor azulada

Ao selecionar arquivos, botões para "deletar", "mover" e "copiar" aparecem no lugar da seleção de guias

"mover" e "copiar" respectivamente movem e copiam os arquivos selecionados para o diretório atual


## Linha de comando
O programa aceita alguns argumentos de linha de comando

- -h: Mostra os comandos disponíveis
- -b x: Muda o intervalo entre fetches para x segundos
- -f x: Muda o intervalo entre updates do front end para x segundos
- -fps x: Muda o FPS (Equivalente a -f 1/x)
- -p: Faz com que as porcentagens apareçam antes das barras
- -t x: Muda o título do programa para x
- -l: Ativa logging (incompleto)
- -d: Ativa o modo de debug (botões aparecem em vermelho)
