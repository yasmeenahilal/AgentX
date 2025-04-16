import sqlite3

from database import get_index_name_type_db
from fastapi import HTTPException
from schemas.agent_schemas import CreateAgentRequest, DeleteAgent, UpdateAgentRequest

from .database import DATABASE


def create_rag_db(request: CreateAgentRequest):
    """
    Create a new Agent entry in the database.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO multi_agent (
                    agent_name, user_id, index_name,
                    llm_provider, llm_model_name, llm_api_key, prompt_template
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    request.agent_name,
                    request.user_id,
                    request.index_name,
                    request.llm_provider,
                    request.llm_model_name,
                    request.llm_api_key,
                    request.prompt_template,
                ),
            )
            conn.commit()
        return f"Agent settings for index '{request.index_name}' created successfully."
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=400,
            detail=f"Agent settings for index '{request.index_name}' already exist.",
        )


def update_rag_db(request: UpdateAgentRequest):
    """
    Update existing Agent settings in the database.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()

            # First, get the current agent details to get the index_name if not provided
            if not request.index_name:
                cursor.execute(
                    """
                    SELECT index_name FROM multi_agent 
                    WHERE user_id = ? AND agent_name = ?
                    """,
                    (request.user_id, request.agent_name),
                )
                result = cursor.fetchone()
                if not result:
                    raise HTTPException(
                        status_code=404,
                        detail=f"No Agent found for user_id '{request.user_id}' and agent_name '{request.agent_name}'.",
                    )
                index_name = result[0]
            else:
                index_name = request.index_name

            # Update multi_agent table
            update_fields = []
            update_values = []

            if request.index_name:
                update_fields.append("index_name = ?")
                update_values.append(request.index_name)
            if request.llm_provider:
                update_fields.append("llm_provider = ?")
                update_values.append(request.llm_provider)
            if request.llm_model_name:
                update_fields.append("llm_model_name = ?")
                update_values.append(request.llm_model_name)
            if request.llm_api_key:
                update_fields.append("llm_api_key = ?")
                update_values.append(request.llm_api_key)
            if request.prompt_template:
                update_fields.append("prompt_template = ?")
                update_values.append(request.prompt_template)

            # If we have fields to update in the multi_agent table
            if update_fields:
                update_values.extend([request.user_id, request.agent_name])
                update_query = f"""
                    UPDATE multi_agent
                    SET {', '.join(update_fields)}
                    WHERE user_id = ? AND agent_name = ?
                """
                cursor.execute(update_query, tuple(update_values))
                
                if cursor.rowcount == 0:
                    raise HTTPException(
                        status_code=404,
                        detail=f"No Agent settings found for user_id '{request.user_id}' and agent_name '{request.agent_name}'.",
                    )

            # Update embeddings_model if provided
            if request.embeddings_model:
                # Get the index type
                index_type = get_index_name_type_db(request.user_id, index_name)
                if not index_type:
                    raise HTTPException(
                        status_code=404,
                        detail=f"No index type found for user_id '{request.user_id}' and index_name '{index_name}'.",
                    )
                
                # Determine which table to update
                table_name = "pinecone_db" if index_type == "Pinecone" else "faiss_db"
                
                # Update the embedding in the appropriate table
                embed_update_query = f"""
                    UPDATE {table_name}
                    SET embedding = ?
                    WHERE user_id = ? AND index_name = ?
                """
                cursor.execute(embed_update_query, (request.embeddings_model, request.user_id, index_name))
                
                if cursor.rowcount == 0:
                    raise HTTPException(
                        status_code=404,
                        detail=f"No embedding found in {table_name} for user_id '{request.user_id}' and index_name '{index_name}'.",
                    )

            # Commit all changes
            conn.commit()
            
            return f"Agent settings for '{request.agent_name}' updated successfully."
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def delete_rag_db(request: DeleteAgent):
    """
    Delete Agent settings from the database, checking if the record exists.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()

            # Check if the agent settings exist
            cursor.execute(
                """
                SELECT 1 FROM multi_agent WHERE user_id = ? AND agent_name = ? LIMIT 1
                """,
                (request.user_id, request.agent_name),
            )
            result = cursor.fetchone()

            if not result:
                # If no record is found, return a message with 404 status code
                return {"message": f"Agent '{request.agent_name}' not found for user '{request.user_id}'"}, 404

            # If record exists, proceed with deletion
            cursor.execute(
                """
                DELETE FROM multi_agent WHERE user_id = ? AND agent_name = ?
                """,
                (request.user_id, request.agent_name),
            )
            conn.commit()

        return {"message": f"Agent settings for index '{request.agent_name}' deleted successfully."}, 200
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_rag_settings(user_id: str, agent_name: str):
    """
    Retrieves Agent settings from the database based on user_id.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()

            # Step 1: Fetch agent details
            cursor.execute(
                """
                SELECT agent_name, index_name, llm_provider,
                       llm_model_name, llm_api_key, prompt_template
                FROM multi_agent WHERE user_id = ? AND agent_name = ?
                """,
                (user_id, agent_name),
            )
            print(user_id, agent_name)
            result = cursor.fetchone()
            # if not result:
            #     raise Exception("Agent not found")
            
            if not result:
                raise Exception("No Agent Found")
                
            print("\n\n\n",result[1])
            index_type = get_index_name_type_db(user_id, result[1])
            print("index type",index_type)
            if not index_type:
                raise Exception("Database type not found")

            # Step 3: Determine the database type (Pinecone or FAISS)
            database_final = "pinecone_db" if index_type == "Pinecone" else "faiss_db"

            # Step 4: Select embedding based on the database type
            # Dynamic SQL query to select embeddings from the appropriate table
            query = f"""
                SELECT embedding FROM {database_final} WHERE user_id = ? AND index_name = ?
            """
            cursor.execute(query, (user_id, result[1]))
            embedding = cursor.fetchone()

            # If embeddings are found, include it in the result
            if embedding:
                result = result + (embedding[0],)  # Append the embedding to the result
                
            
            # Combine the results and column names
            return {
                "data": result,
                "index_type": index_type
            }
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    # except sqlite3.Error as e:
    #     raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


def get_all_agents_for_user(user_id: str):
    """
    Retrieves all Agents for a specific user from the database.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()

            # Fetch all agents for the user
            cursor.execute(
                """
                SELECT agent_name, index_name, llm_provider, 
                       llm_model_name, prompt_template 
                FROM multi_agent 
                WHERE user_id = ?
                """,
                (user_id,)
            )
            results = cursor.fetchall()
            
            # Get column names
            cursor.execute("PRAGMA table_info(multi_agent)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # We're excluding llm_api_key for security reasons
            display_columns = [col for col in columns if col != 'llm_api_key' and col != 'id' and col != 'user_id']
            
            # Format results as a list of dictionaries
            agents = []
            for result in results:
                # Create a dict with column names and values, excluding API key
                agent_data = {
                    "agent_name": result[0],
                    "index_name": result[1],
                    "llm_provider": result[2],
                    "llm_model_name": result[3],
                    "prompt_template": result[4]
                }
                agents.append(agent_data)
            
            return {
                "agents": agents,
                "columns": display_columns
            }
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
