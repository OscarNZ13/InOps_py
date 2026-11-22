% Reglas de Iniciales y Firma (seccion 5 del contexto).
% Python entrega el texto ya normalizado (sin acentos ni signos) y aporta used/1,
% que consulta si un valor ya esta ocupado.

first_letter(Text, Letter) :-
    split_string(Text, " ", " ", [First|_]),
    sub_atom(First, 0, 1, _, Char),
    upcase_atom(Char, Letter).

without_spaces(Text, Joined) :-
    split_string(Text, " ", " ", Words),
    atomic_list_concat(Words, Joined).

capitalized(Text, Capitalized) :-
    sub_atom(Text, 0, 1, _, Head),
    sub_atom(Text, 1, _, 0, Tail),
    upcase_atom(Head, Upper),
    downcase_atom(Tail, Lower),
    atom_concat(Upper, Lower, Capitalized).

% El orden de las clausulas es la prioridad y el corte evita probar las siguientes.
% Si el primer apellido tiene menos de 2 letras, la tercera clausula falla.
extra_letter(SecondLastName, _, _, Letter) :-
    SecondLastName \== '', !,
    first_letter(SecondLastName, Letter).
extra_letter(_, SecondName, _, Letter) :-
    SecondName \== '', !,
    first_letter(SecondName, Letter).
extra_letter(_, _, LastName, Letter) :-
    without_spaces(LastName, Joined),
    sub_atom(Joined, 1, 1, _, Char),
    upcase_atom(Char, Letter).

% Backtracking sobre between/3: prueba Base1, Base2... hasta que used/1 no se pueda demostrar
available(Base, Base) :-
    \+ used(Base), !.
available(Base, Candidate) :-
    between(1, inf, N),
    atom_concat(Base, N, Candidate),
    \+ used(Candidate), !.

initials(FirstName, LastName, Extra, Initials) :-
    first_letter(FirstName, First),
    first_letter(LastName, Last),
    atomic_list_concat([First, Last, Extra], Base),
    available(Base, Initials).

signature(FirstName, LastName, Extra, Signature) :-
    first_letter(FirstName, First),
    without_spaces(LastName, Joined),
    capitalized(Joined, Capitalized),
    atom_concat(First, Capitalized, Base),
    signature_from(Base, Extra, Signature).

signature_from(Base, _, Base) :-
    \+ used(Base), !.
signature_from(Base, Extra, Signature) :-
    atom_concat(Base, Extra, WithExtra),
    available(WithExtra, Signature).
