from datetime import datetime
from uuid import uuid4
from typing import List, Optional
from fastapi import APIRouter, Body, HTTPException, Query, Depends, status
from pydantic import UUID4
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi_pagination import Page, add_pagination, paginate
from WorkOutApi.atleta.models import AtletaModel
from WorkOutApi.atleta.schemas import AtletaIn, AtletaOut, AtletaUpdate
from WorkOutApi.categorias.models import CategoriaModel
from WorkOutApi.centro_treinamento.models import CentroTreinamentoModel
from WorkOutApi.contrib.dependencies import DatabaseDependency

router = APIRouter()

@router.post(
    "/",
    summary="Criar um novo Atleta",
    status_code=status.HTTP_201_CREATED,
    response_model=AtletaOut
)
async def post(
    db_session: DatabaseDependency,
    atleta_in: AtletaIn = Body(...),
):
    categoria_name = atleta_in.categoria.nome
    centro_treinamento_name = atleta_in.centro_treinamento.nome

    categoria = (await db_session.execute(
        select(CategoriaModel).filter_by(nome=categoria_name))
    ).scalars().first()

    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Categoria '{categoria_name}' não encontrada"
        )

    centro_treinamento = (await db_session.execute(
        select(CentroTreinamentoModel).filter_by(nome=centro_treinamento_name))
    ).scalars().first()

    if not centro_treinamento:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Centro de Treinamento '{centro_treinamento_name}' não encontrado"
        )

    try:
        atleta_out = AtletaOut(id=uuid4(), creat_at=datetime.now(), **atleta_in.model_dump())
        atleta_model = AtletaModel(**atleta_out.model_dump(exclude={"categoria", "centro_treinamento"}))

        atleta_model.categoria_id = categoria.pk_id
        atleta_model.centro_treinamento_id = centro_treinamento.pk_id

        db_session.add(atleta_model)
        await db_session.commit()

    except IntegrityError as e:
        if "duplicate key value violates unique constraint" in str(e):
            raise HTTPException(
                status_code=status.HTTP_303_SEE_OTHER,
                detail=f"Já existe um atleta cadastrado com o CPF: {atleta_in.cpf}",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ocorreu um erro ao inserir o dado no banco"
            )

    return atleta_out


@router.get(
    "/",
    summary="Consultar alteta pelo nome e cpf",
    status_code=status.HTTP_200_OK,
    response_model=List[AtletaOut],
)
async def query_all_atletas(
    db_session: DatabaseDependency,
    nome: Optional[str] = Query(None, description="Filtrar por nome do atleta"),
    cpf: Optional[str] = Query(None, description="Filtrar por CPF do atleta"),
) -> List[AtletaOut]:
    query = select(AtletaModel)

    if nome:
        query = query.filter(AtletaModel.nome.ilike(f"%{nome}%"))

    if cpf:
        query = query.filter(AtletaModel.cpf == cpf)

    atletas = (await db_session.execute(query)).scalars().all()

    return [AtletaOut.model_validate(atleta) for atleta in atletas]


@router.get(
    "/{id}",
    summary="Consultar um atleta pelo ID",
    status_code=status.HTTP_200_OK,
    response_model=AtletaOut,
)
async def query_atleta_by_id(
    id: UUID4,
    db_session: DatabaseDependency,
) -> AtletaOut:
    atleta = (await db_session.execute(select(AtletaModel).filter_by(id=id))).scalars().first()

    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Atleta não encontrado com o ID: {id}"
        )

    return AtletaOut.model_validate(atleta)


@router.patch(
    "/{id}",
    summary="Editar um atleta pelo ID",
    status_code=status.HTTP_200_OK,
    response_model=AtletaOut,
)
async def update_atleta(
    id: UUID4,
    db_session: DatabaseDependency,
    atleta_up: AtletaUpdate = Body(...),
) -> AtletaOut:
    atleta = (await db_session.execute(select(AtletaModel).filter_by(id=id))).scalars().first()

    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Atleta não encontrado com o ID: {id}"
        )

    atleta_update = atleta_up.model_dump(exclude_unset=True)
    for key, value in atleta_update.items():
        setattr(atleta, key, value)

    await db_session.commit()
    await db_session.refresh(atleta)

    return AtletaOut.model_validate(atleta)


@router.delete(
    "/{id}",
    summary="Deletar um atleta pelo ID",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_atleta(
    id: UUID4,
    db_session: DatabaseDependency,
) -> None:
    atleta = (await db_session.execute(select(AtletaModel).filter_by(id=id))).scalars().first()

    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Atleta não encontrado com o ID: {id}"
        )

    await db_session.delete(atleta)
    await db_session.commit()

add_pagination(router)
