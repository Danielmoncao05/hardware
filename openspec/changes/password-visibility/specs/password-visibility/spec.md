## ADDED Requirements

### Requirement: Mostrar e ocultar a senha digitada
Todo campo de senha do app (login, definir nova senha pelo link de e-mail, alterar senha e senha temporária de novo usuário) DEVE ter um botão com ícone de olho dentro do campo que alterna entre mostrar e ocultar o que foi digitado. O campo DEVE começar oculto ao abrir a tela e DEVE voltar a ficar oculto quando o formulário é enviado. Cada campo DEVE ter o seu próprio controle. O botão DEVE ser operável pelo teclado, DEVE ter rótulo acessível que descreve a ação ("Mostrar senha" ou "Ocultar senha") e indicar se está ativo, e NÃO DEVE enviar o formulário. Alternar a visibilidade NÃO DEVE enviar a senha ao servidor nem guardá-la no estado do app, e NÃO DEVE atrapalhar o preenchimento automático dos gerenciadores de senha.

#### Scenario: Conferir a senha no login
- **QUANDO** o usuário digita a senha no login e clica no ícone de olho
- **ENTÃO** o app DEVE mostrar a senha em texto, trocar o ícone para olho riscado e o rótulo do botão para "Ocultar senha"

#### Scenario: Ocultar de novo
- **QUANDO** a senha está visível e o usuário clica de novo no botão
- **ENTÃO** o app DEVE ocultar a senha, voltar ao ícone de olho e ao rótulo "Mostrar senha"

#### Scenario: Controles independentes
- **QUANDO** o usuário mostra a nova senha na tela Alterar senha
- **ENTÃO** a senha atual e a confirmação DEVEM continuar ocultas

#### Scenario: Pelo teclado, sem enviar o formulário
- **QUANDO** o usuário chega ao botão com Tab e pressiona Enter ou Espaço
- **ENTÃO** o app DEVE alternar a visibilidade da senha e NÃO DEVE enviar o formulário

#### Scenario: Oculta depois do envio
- **QUANDO** o usuário envia o formulário com a senha visível e o app mostra um erro de validação
- **ENTÃO** os campos de senha DEVEM estar ocultos de novo
