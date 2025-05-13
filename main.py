from mcp.server.fastmcp import FastMCP
import requests
import json
import asyncio
from typing import Dict, List, Optional, Any, Union
from decouple import config

mcp = FastMCP("Notion - Manager",)
BASE_URL = "https://api.notion.com/v1/"
_headers = {
    "Authorization": f"Bearer {config('NOTIO_API_KEY')}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

@mcp.tool()
def notion_query_databases(filter: Optional[Dict] = None, sorts: Optional[List] = None, 
                           start_cursor: Optional[str] = None, page_size: int = 100, data_base_id:str=None) -> Dict:
    """
    Consulta um banco de dados do Notion com filtros e ordenação.
    
    Args:
        filter: Dicionário com filtros para a consulta
        sorts: Lista de ordenações para os resultados
        start_cursor: Cursor para paginação
        page_size: Número máximo de resultados por página
    
    Returns:
        Resultados da consulta ao banco de dados
    """
    url = f"{BASE_URL}databases/{data_base_id}/query"
    
    body = {}
    if filter:
        body["filter"] = filter
    if sorts:
        body["sorts"] = sorts
    if start_cursor:
        body["start_cursor"] = start_cursor
    if page_size:
        body["page_size"] = page_size
    
    response = requests.post(url, headers=_headers, json=body)
    
    if response.status_code != 200:
        return {"error": f"Erro {response.status_code}: {response.text}"}
    
    return response.json()

@mcp.tool()
def get_notion_page(page_id: str) -> Dict:
    """
    Recupera uma página específica do Notion pelo ID.
    
    Args:
        page_id: ID da página do Notion
    
    Returns:
        Dados da página
    """
    # Remover hífens e outros caracteres se o ID não estiver no formato correto
    page_id = page_id.replace("-", "")
    
    url = f"{BASE_URL}pages/{page_id}"
    response = requests.get(url, headers=_headers)
    
    if response.status_code != 200:
        return {"error": f"Erro {response.status_code}: {response.text}"}
    
    return response.json()

@mcp.tool()
def get_page_content(page_id: str) -> Dict:
    """
    Recupera o conteúdo (blocos) de uma página específica do Notion.
    
    Args:
        page_id: ID da página do Notion
    
    Returns:
        Conteúdo da página (blocos)
    """
    # Remover hífens e outros caracteres se o ID não estiver no formato correto
    page_id = page_id.replace("-", "")
    
    url = f"{BASE_URL}blocks/{page_id}/children"
    response = requests.get(url, headers=_headers)
    
    if response.status_code != 200:
        return {"error": f"Erro {response.status_code}: {response.text}"}
    
    return response.json()

@mcp.tool()
def get_page_content_optimized(page_id: str, max_depth: int = 1, 
                               max_blocks: int = 100) -> Dict:
    """
    Versão otimizada para buscar conteúdo da página com controle de profundidade.
    
    Args:
        page_id: ID da página do Notion
        max_depth: Profundidade máxima de blocos aninhados
        max_blocks: Número máximo de blocos a recuperar
        
    Returns:
        Conteúdo formatado da página
    """
    page_id = page_id.replace("-", "")
    url = f"{BASE_URL}blocks/{page_id}/children?page_size={max_blocks}"
    
    response = requests.get(url, headers=_headers)
    
    if response.status_code != 200:
        return {"error": f"Erro {response.status_code}: {response.text}"}
    
    data = response.json()
    
    # Processar blocos de primeiro nível
    formatted_blocks = []
    for block in data.get("results", []):
        formatted_block = format_block(block)
        
        # Buscar blocos filhos apenas se não exceder a profundidade máxima
        if max_depth > 1 and block.get("has_children", False):
            try:
                child_blocks = get_page_content_optimized(
                    block["id"], max_depth - 1, max_blocks=50
                )
                if "error" not in child_blocks:
                    formatted_block["children"] = child_blocks.get("blocks", [])
            except Exception as e:
                formatted_block["children_error"] = str(e)
        
        formatted_blocks.append(formatted_block)
    
    return {
        "blocks": formatted_blocks,
        "count": len(formatted_blocks),
        "has_more": data.get("has_more", False)
    }

@mcp.tool()
def get_paginated_content(page_id: str, max_blocks: int = 1000) -> Dict:
    """
    Recupera o conteúdo de uma página usando paginação para páginas grandes.
    
    Args:
        page_id: ID da página do Notion
        max_blocks: Número máximo de blocos a recuperar
        
    Returns:
        Conteúdo da página (blocos)
    """
    page_id = page_id.replace("-", "")
    url = f"{BASE_URL}blocks/{page_id}/children"
    
    results = []
    start_cursor = None
    count = 0
    
    while count < max_blocks:
        params = {"page_size": 100}  # Usar blocos menores de 100 para cada solicitação
        if start_cursor:
            params["start_cursor"] = start_cursor
            
        response = requests.get(url, headers=_headers, params=params)
        
        if response.status_code != 200:
            return {"error": f"Erro {response.status_code}: {response.text}"}
        
        data = response.json()
        block_results = data.get("results", [])
        results.extend(block_results)
        count += len(block_results)
        
        if not data.get("has_more", False):
            break
            
        start_cursor = data.get("next_cursor")
        if not start_cursor:
            break
    
    return {"results": results, "count": count}

@mcp.tool()
def update_page_properties(page_id: str, properties: Dict) -> Dict:
    """
    Atualiza as propriedades de uma página do Notion.
    
    Args:
        page_id: ID da página do Notion
        properties: Propriedades a serem atualizadas
    
    Returns:
        Página atualizada
    """
    page_id = page_id.replace("-", "")
    
    url = f"{BASE_URL}pages/{page_id}"
    body = {"properties": properties}
    
    response = requests.patch(url, headers=_headers, json=body)
    
    if response.status_code != 200:
        return {"error": f"Erro {response.status_code}: {response.text}"}
    
    return response.json()

@mcp.tool()
def create_page(parent_id: str, properties: Dict, content: Optional[List] = None, 
                is_database: bool = True) -> Dict:
    """
    Cria uma nova página no Notion.
    
    Args:
        parent_id: ID do banco de dados ou página pai
        properties: Propriedades da página
        content: Conteúdo (blocos) da página
        is_database: Se True, o parent_id é um banco de dados
    
    Returns:
        Nova página criada
    """
    parent_id = parent_id.replace("-", "")
    
    url = f"{BASE_URL}pages"
    body = {
        "parent": {"database_id": parent_id} if is_database else {"page_id": parent_id},
        "properties": properties
    }
    
    if content:
        body["children"] = content
    
    response = requests.post(url, headers=_headers, json=body)
    
    if response.status_code != 200:
        return {"error": f"Erro {response.status_code}: {response.text}"}
    
    return response.json()

@mcp.tool()
def append_page_content(page_id: str, blocks: List) -> Dict:
    """
    Adiciona conteúdo a uma página existente.
    
    Args:
        page_id: ID da página
        blocks: Lista de blocos a serem adicionados
    
    Returns:
        Resposta da API
    """
    page_id = page_id.replace("-", "")
    
    url = f"{BASE_URL}blocks/{page_id}/children"
    body = {"children": blocks}
    
    response = requests.patch(url, headers=_headers, json=body)
    
    if response.status_code != 200:
        return {"error": f"Erro {response.status_code}: {response.text}"}
    
    return response.json()

@mcp.tool()
def search_notion(query: str, filter_type: Optional[str] = None, 
                  sort: Optional[Dict] = None, page_size: int = 100) -> Dict:
    """
    Pesquisa no Notion por páginas, bancos de dados ou blocos.
    
    Args:
        query: Termo de pesquisa
        filter_type: Tipo de objeto a ser pesquisado (page, database, etc.)
        sort: Ordenação dos resultados
        page_size: Número máximo de resultados
    
    Returns:
        Resultados da pesquisa
    """
    url = f"{BASE_URL}search"
    
    body = {"query": query, "page_size": page_size}
    
    if filter_type:
        body["filter"] = {"value": filter_type, "property": "object"}
    
    if sort:
        body["sort"] = sort
    
    response = requests.post(url, headers=_headers, json=body)
    
    if response.status_code != 200:
        return {"error": f"Erro {response.status_code}: {response.text}"}
    
    return response.json()

@mcp.tool()
def parse_page_content(content_response: Dict) -> Dict:
    """
    Analisa e formata o conteúdo de uma página para melhor legibilidade.
    
    Args:
        content_response: Resposta da API com os blocos da página
    
    Returns:
        Conteúdo formatado da página
    """
    if "results" not in content_response:
        return {"error": "Formato de resposta inválido"}
    
    results = content_response["results"]
    formatted_content = []
    
    for block in results:
        block_type = block.get("type")
        if not block_type:
            continue
            
        block_data = block.get(block_type, {})
        
        if block_type == "paragraph":
            text_content = extract_text_from_rich_text(block_data.get("rich_text", []))
            if text_content:
                formatted_content.append({"type": "paragraph", "content": text_content})
        
        elif block_type == "heading_1":
            text_content = extract_text_from_rich_text(block_data.get("rich_text", []))
            if text_content:
                formatted_content.append({"type": "heading_1", "content": text_content})
        
        elif block_type == "heading_2":
            text_content = extract_text_from_rich_text(block_data.get("rich_text", []))
            if text_content:
                formatted_content.append({"type": "heading_2", "content": text_content})
        
        elif block_type == "heading_3":
            text_content = extract_text_from_rich_text(block_data.get("rich_text", []))
            if text_content:
                formatted_content.append({"type": "heading_3", "content": text_content})
        
        elif block_type == "bulleted_list_item":
            text_content = extract_text_from_rich_text(block_data.get("rich_text", []))
            if text_content:
                formatted_content.append({"type": "bulleted_list_item", "content": text_content})
        
        elif block_type == "numbered_list_item":
            text_content = extract_text_from_rich_text(block_data.get("rich_text", []))
            if text_content:
                formatted_content.append({"type": "numbered_list_item", "content": text_content})
        
        elif block_type == "to_do":
            text_content = extract_text_from_rich_text(block_data.get("rich_text", []))
            checked = block_data.get("checked", False)
            if text_content:
                formatted_content.append({
                    "type": "to_do", 
                    "content": text_content, 
                    "checked": checked
                })
        
        elif block_type == "code":
            text_content = extract_text_from_rich_text(block_data.get("rich_text", []))
            language = block_data.get("language", "")
            if text_content:
                formatted_content.append({
                    "type": "code", 
                    "content": text_content, 
                    "language": language
                })
        
        elif block_type == "image":
            url = None
            if "file" in block_data:
                url = block_data["file"].get("url")
            elif "external" in block_data:
                url = block_data["external"].get("url")
                
            if url:
                formatted_content.append({"type": "image", "url": url})
        
        elif block_type == "divider":
            formatted_content.append({"type": "divider"})
        
        elif block_type == "table":
            formatted_content.append({"type": "table", "info": "Table content requires additional processing"})
    
    return {"formatted_content": formatted_content}

def extract_text_from_rich_text(rich_text: List) -> str:
    """
    Extrai texto de uma array de objetos rich_text do Notion.
    
    Args:
        rich_text: Lista de objetos rich_text
        
    Returns:
        Texto extraído
    """
    text_parts = []
    
    for text_obj in rich_text:
        if "text" in text_obj and "content" in text_obj["text"]:
            text_parts.append(text_obj["text"]["content"])
    
    return " ".join(text_parts)

def format_block(block: Dict) -> Dict:
    """
    Formata um bloco individual para uma representação simplificada.
    
    Args:
        block: Bloco da API do Notion
        
    Returns:
        Versão formatada do bloco
    """
    block_id = block.get("id", "")
    block_type = block.get("type", "unknown")
    has_children = block.get("has_children", False)
    
    formatted = {
        "id": block_id,
        "type": block_type,
        "has_children": has_children
    }
    
    # Extrair conteúdo baseado no tipo
    if block_type in block:
        content_data = block[block_type]
        
        # Extrair texto para tipos comuns
        if "rich_text" in content_data:
            formatted["text"] = extract_text_from_rich_text(content_data["rich_text"])
        
        # Adicionar metadados específicos por tipo
        if block_type == "to_do":
            formatted["checked"] = content_data.get("checked", False)
        
        elif block_type == "code":
            formatted["language"] = content_data.get("language", "")
        
        elif block_type == "image":
            if "file" in content_data:
                formatted["url"] = content_data["file"].get("url", "")
            elif "external" in content_data:
                formatted["url"] = content_data["external"].get("url", "")
    
    return formatted

@mcp.tool()
def get_task_details(task_id: str) -> Dict:
    """
    Obtém detalhes completos de uma tarefa, incluindo propriedades e conteúdo.
    
    Args:
        task_id: ID da página/tarefa
    
    Returns:
        Detalhes completos da tarefa
    """
    # Obter propriedades da página
    page_data = get_notion_page(task_id)
    
    if "error" in page_data:
        return page_data
    
    # Obter conteúdo da página - versão otimizada
    content_data = get_page_content_optimized(task_id, max_depth=2)
    
    if "error" in content_data:
        return {
            "page": page_data,
            "content_error": content_data["error"]
        }
    
    # Simplificar os dados da página para facilitar o acesso
    properties = page_data.get("properties", {})
    
    simplified_task = {
        "id": page_data.get("id", ""),
        "title": extract_title(properties.get("Title", {})),
        "status": extract_status(properties.get("Status", {})),
        "owner": extract_people_names(properties.get("Owner", {})),
        "team": extract_people_names(properties.get("Team", {})),
        "system": extract_select(properties.get("System", {})),
        "last_update": properties.get("Last update", {}).get("last_edited_time", ""),
        "created_at": properties.get("Created at", {}).get("created_time", ""),
        "tags": extract_multi_select(properties.get("Tags", {})),
        "description": extract_rich_text(properties.get("Description", {})),
        "content": content_data.get("blocks", [])
    }
    
    return simplified_task

@mcp.tool()
def get_filtered_tasks(status: Optional[str] = None, owner_email: Optional[str] = None, 
                       system: Optional[str] = None, limit: int = 10) -> Dict:
    """
    Busca tarefas com filtros combinados e limite de resultados para otimização.
    
    Args:
        status: Status desejado (opcional)
        owner_email: Email do proprietário (opcional)
        system: Nome do sistema (opcional)
        limit: Número máximo de resultados
        
    Returns:
        Lista filtrada de tarefas
    """
    filters = []
    
    if status:
        filters.append(create_status_filter(status))
    
    if owner_email:
        filters.append(create_owner_filter(owner_email))
        
    if system:
        filters.append({
            "property": "System",
            "select": {
                "equals": system
            }
        })
    
    filter_query = {}
    if filters:
        filter_query = create_combined_filter(filters)
    
    # Adicionar ordenação para obter as tarefas mais recentes
    sorts = [{"property": "Last update", "direction": "descending"}]
    
    # Limitar número de resultados
    result = notion_query_databases(
        filter=filter_query, 
        sorts=sorts,
        page_size=limit
    )
    
    # Extrair apenas as informações essenciais para cada tarefa
    simplified_tasks = []
    for page in result.get("results", []):
        properties = page.get("properties", {})
        
        task = {
            "id": page.get("id", ""),
            "title": extract_title(properties.get("Title", {})),
            "status": extract_status(properties.get("Status", {})),
            "owner": extract_people_names(properties.get("Owner", {})),
            "team": extract_people_names(properties.get("Team", {})),
            "system": extract_select(properties.get("System", {})),
            "last_update": properties.get("Last update", {}).get("last_edited_time", "")
        }
        
        simplified_tasks.append(task)
    
    return {
        "tasks": simplified_tasks,
        "count": len(simplified_tasks),
        "has_more": result.get("has_more", False)
    }

# Funções auxiliares para extração de dados
def extract_title(title_prop: Dict) -> str:
    """Extrai o texto do título de uma propriedade Title"""
    title_array = title_prop.get("title", [])
    if not title_array:
        return ""
    
    return " ".join([t.get("plain_text", "") for t in title_array])

def extract_status(status_prop: Dict) -> str:
    """Extrai o nome do status de uma propriedade Status"""
    status = status_prop.get("status", {})
    return status.get("name", "") if status else ""

def extract_people_names(people_prop: Dict) -> List[str]:
    """Extrai nomes de pessoas de uma propriedade People"""
    people_array = people_prop.get("people", [])
    return [person.get("name", "") for person in people_array if "name" in person]

def extract_select(select_prop: Dict) -> str:
    """Extrai o valor de uma propriedade Select"""
    select = select_prop.get("select", {})
    return select.get("name", "") if select else ""

def extract_multi_select(multi_select_prop: Dict) -> List[str]:
    """Extrai valores de uma propriedade Multi-select"""
    multi_select_array = multi_select_prop.get("multi_select", [])
    return [option.get("name", "") for option in multi_select_array if "name" in option]

def extract_rich_text(rich_text_prop: Dict) -> str:
    """Extrai texto de uma propriedade Rich Text"""
    rich_text_array = rich_text_prop.get("rich_text", [])
    return extract_text_from_rich_text(rich_text_array)

# Funções para criar filtros
@mcp.tool()
def create_status_filter(status: str) -> Dict:
    """
    Cria um filtro para o status da tarefa.
    
    Args:
        status: Status desejado (ex: "To Do", "Doing", "Done")
    
    Returns:
        Filtro para ser usado na consulta
    """
    return {
        "property": "Status",
        "status": {
            "equals": status
        }
    }

@mcp.tool()
def create_owner_filter_by_name(person_name: str) -> Dict:
    """
    Cria um filtro para o proprietário da tarefa usando o nome.
    
    Args:
        person_name: Nome da pessoa (parcial ou completo)
    
    Returns:
        Filtro para ser usado na consulta
    """
    return {
        "property": "Owner",
        "people": {
            "contains": person_name
        }
    }

@mcp.tool()
def create_team_member_filter(person_name: str) -> Dict:
    """
    Cria um filtro para encontrar tarefas onde a pessoa é membro da equipe.
    
    Args:
        person_name: Nome da pessoa (parcial ou completo)
    
    Returns:
        Filtro para ser usado na consulta
    """
    return {
        "property": "Team",
        "people": {
            "contains": person_name
        }
    }

@mcp.tool()
def create_text_contains_filter(property_name: str, value: str) -> Dict:
    """
    Cria um filtro genérico para qualquer propriedade de texto que contenha um valor.
    
    Args:
        property_name: Nome da propriedade (ex: "Title", "Description")
        value: Valor que a propriedade deve conter
    
    Returns:
        Filtro para ser usado na consulta
    """
    return {
        "property": property_name,
        "rich_text": {
            "contains": value
        }
    }

@mcp.tool()
def find_tasks_by_person(person_name: str, role: str = "any", limit: int = 20) -> Dict:
    """
    Encontra tarefas associadas a uma pessoa, seja como dono ou membro da equipe.
    
    Args:
        person_name: Nome da pessoa (parcial ou completo)
        role: "owner" para buscar apenas como dono, "team" para apenas como membro da equipe,
              "any" para ambos os casos (padrão)
        limit: Número máximo de resultados
    
    Returns:
        Lista de tarefas associadas à pessoa
    """
    filters = []
    
    if role == "owner" or role == "any":
        filters.append(create_owner_filter_by_name(person_name))
    
    if role == "team" or role == "any":
        filters.append(create_team_member_filter(person_name))
    
    # Se estamos buscando por owner E team, usamos OR para combiná-los
    if role == "any":
        filter_query = create_combined_filter(filters, "or")
    else:
        # Se estamos buscando apenas owner OU apenas team, usamos AND 
        # (embora com apenas um filtro não faz diferença)
        filter_query = create_combined_filter(filters, "and")
    
    # Ordenar por atualização mais recente
    sorts = [{"property": "Last update", "direction": "descending"}]
    
    result = notion_query_databases(
        filter=filter_query,
        sorts=sorts,
        page_size=limit
    )
    
    # Processar resultados para formato mais legível
    tasks = []
    for page in result.get("results", []):
        properties = page.get("properties", {})
        
        # Verificar se a pessoa é dono ou membro da equipe
        is_owner = False
        is_team_member = False
        
        owner_names = extract_people_names(properties.get("Owner", {}))
        team_names = extract_people_names(properties.get("Team", {}))
        
        for name in owner_names:
            if person_name.lower() in name.lower():
                is_owner = True
                break
                
        for name in team_names:
            if person_name.lower() in name.lower():
                is_team_member = True
                break
        
        task = {
            "id": page.get("id", ""),
            "title": extract_title(properties.get("Title", {})),
            "status": extract_status(properties.get("Status", {})),
            "system": extract_select(properties.get("System", {})),
            "last_update": properties.get("Last update", {}).get("last_edited_time", ""),
            "is_owner": is_owner,
            "is_team_member": is_team_member,
            "owners": owner_names,
            "team": team_names
        }
        
        tasks.append(task)
    
    return {
        "tasks": tasks,
        "count": len(tasks),
        "has_more": result.get("has_more", False),
        "filter_used": {"person_name": person_name, "role": role}
    }

@mcp.tool()
def list_people_in_database(limit: int = 50) -> Dict:
    """
    Lista todas as pessoas (donos e membros de equipe) encontradas no banco de dados.
    
    Args:
        limit: Número máximo de páginas a verificar
        
    Returns:
        Lista de pessoas únicas no banco de dados
    """
    # Buscar as tarefas mais recentemente atualizadas
    result = notion_query_databases(
        sorts=[{"property": "Last update", "direction": "descending"}],
        page_size=limit
    )
    
    people_dict = {}  # Usar dicionário para evitar duplicatas
    
    for page in result.get("results", []):
        properties = page.get("properties", {})
        
        # Coletar donos
        owners = extract_people_names(properties.get("Owner", {}))
        for person in owners:
            if person and person not in people_dict:
                people_dict[person] = {"name": person, "roles": ["owner"]}
            elif person and "owner" not in people_dict[person]["roles"]:
                people_dict[person]["roles"].append("owner")
        
        # Coletar membros da equipe
        team_members = extract_people_names(properties.get("Team", {}))
        for person in team_members:
            if person and person not in people_dict:
                people_dict[person] = {"name": person, "roles": ["team"]}
            elif person and "team" not in people_dict[person]["roles"]:
                people_dict[person]["roles"].append("team")
    
    # Converter dicionário para lista
    people_list = list(people_dict.values())
    
    # Ordenar por nome
    people_list.sort(key=lambda x: x["name"])
    
    return {
        "people": people_list,
        "count": len(people_list),
        "pages_checked": min(len(result.get("results", [])), limit)
    }

@mcp.tool()
def create_combined_filter(filters: List[Dict], operator: str = "and") -> Dict:
    """
    Combina vários filtros em um único filtro.
    
    Args:
        filters: Lista de filtros
        operator: "and" ou "or"
    
    Returns:
        Filtro combinado
    """
    return {
        operator: filters
    }